import asyncio
import logging
import os
import shutil
from functools import partial, wraps
from pathlib import Path
from typing import Any, Optional

import aiofiles.os
import anitopy

from tsundoku.config import get_config_value
from tsundoku.manager import Entry, EntryState

logger = logging.getLogger("tsundoku")


def wrap(func: Any) -> Any:
    @wraps(func)
    async def run(*args: Any, loop: Any = None, executor: Any = None, **kwargs: Any) -> Any:
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


move = wrap(shutil.move)


class ExprDict(dict):
    """
    A basic wrapping around a dict that,
    when a missing key is requested, will
    simply return the requested key.
    """

    def __missing__(self, value: str) -> str:
        return value


class Downloader:
    """
    Begins handling by adding the torrent to a download client
    and inserting a row into the `show_entry` table.

    The download manager will then check for the
    entry's completion periodically (15 seconds) until
    the item is found to be complete.

    A completed item, once found, will be renamed and then
    subsequently moved to a target destination.

    Finally, the item will be marked as complete in the
    `show_entry` table.
    """

    def __init__(self, app_context: Any) -> None:
        self.app = app_context.app

        self.update_config()

    def update_config(self) -> None:
        """
        Updates the configuration for the task.
        """
        complete_check = get_config_value("Tsundoku", "complete_check_interval", 15)
        try:
            self.complete_check = int(complete_check)
        except ValueError:
            logger.error(f"'{complete_check}' is an invalid complete check interval, using default.")
            self.complete_check = 15

    async def start(self) -> None:
        while True:
            try:
                await self.check_show_entries()
            except Exception:
                import traceback
                traceback.print_exc()

            await asyncio.sleep(self.complete_check)
            self.update_config()

    def get_expression_mapping(self, title: str, season: str, episode: str, **kwargs: str) -> ExprDict:
        """
        Creates an ExprDict of specific expressions to use
        when formatting strings.

        Parameters
        ----------
        title: str
            The title of the show.
        season: str
            The season of the show.
        episode: str
            The episode of the release.
        kwargs:
            Any additional expressions to be
            added to the ExprDict.

        Returns
        -------
        ExprDict
            The expression dict.
        """
        return ExprDict(
            n=title,
            s=season,
            e=episode,
            s00=season.zfill(2),
            e00=episode.zfill(2),
            s00e00=f"s{season.zfill(2)}e{episode.zfill(2)}",
            S00E00=f"S{season.zfill(2)}E{episode.zfill(2)}",
            sxe=f"{season}x{episode.zfill(2)}",
            **kwargs
        )

    async def begin_handling(self, show_id: int, episode: int, magnet_url: str) -> Optional[int]:
        """
        Begins downloading an episode of a show
        using the passed magnet URL.

        Shows downloaded using this method will be
        tracked for moving and renaming purposes.

        Parameters
        ----------
        show_id: int
            The ID of the show in the `shows` table.
        episode: int
            The episode of the show downloading.
        magnet_url: str
            The magnet URL to use to initiate the download.

        Returns
        -------
        Optional[int]:
            The ID of the added entry.
        """
        torrent_hash = await self.app.dl_client.add_torrent(magnet_url)

        if torrent_hash is None:
            logger.warn(
                f"Failed to add Magnet URL {magnet_url} to download client")
            return None

        # TODO: handle entry insertion in the Entry class
        async with self.app.acquire_db() as con:
            await con.execute("""
                INSERT INTO
                    show_entry (
                        show_id,
                        episode,
                        torrent_hash
                    )
                VALUES
                    (?, ?, ?);
            """, show_id, episode, torrent_hash)
            await con.execute("""
                SELECT
                    id,
                    show_id,
                    episode,
                    current_state,
                    torrent_hash,
                    file_path,
                    last_update
                FROM
                    show_entry
                WHERE
                    id = ?;
            """, con.lastrowid)
            entry = await con.fetchone()

        entry = Entry(self.app, entry)
        await entry.set_state(EntryState.downloading)

        logger.info(f"Release Marked as Downloading - {show_id}, {episode}")

        return entry.id

    async def handle_move(self, entry: Entry) -> Optional[Path]:
        """
        Handles the move for a downloaded entry.
        Returns the new pathlib.Path of the moved file.

        Parameters
        ----------
        entry: Entry
            The downloaded entry.

        Returns
        -------
        Optional[pathlib.Path]
            The new path of the moved file.
        """
        if entry.file_path is None:
            logger.error("entry.file_path is None?")
            return None

        async with self.app.acquire_db() as con:
            await con.execute("""
                SELECT
                    title,
                    desired_folder,
                    episode_offset,
                    season
                FROM
                    shows
                WHERE id=?;
            """, entry.show_id)
            show_info = await con.fetchone()

        season = str(show_info["season"])
        episode = str(entry.episode + show_info["episode_offset"])

        expressions = self.get_expression_mapping(
            show_info["title"], season, episode)

        desired_folder = show_info["desired_folder"]
        if desired_folder is None:
            desired_folder = entry.file_path.parent
        else:
            expressive_folder = desired_folder.format_map(expressions)

            Path(expressive_folder).mkdir(parents=True, exist_ok=True)
            desired_folder = Path(expressive_folder)

        name = entry.file_path.name

        try:
            await move(str(entry.file_path), str(desired_folder / name))
        except PermissionError:
            logger.error("Error Moving Release - Invalid Permissions")
        except Exception as e:
            logger.error(f"Error Moving Release - {e}")
        else:
            moved_file = desired_folder / name

            # For now, we simply ignore the creation of trailing symlinks
            # if we're in a Docker environment. This is due to the fact that
            # symlinks are relative and the symlink can be valid or invalid
            # depending on which filesystem it's being checked from.
            is_docker = os.environ.get("IS_DOCKER", False)
            if not is_docker:
                try:
                    entry.file_path.symlink_to(moved_file)
                except Exception as e:
                    logger.warn(f"Failed to Create Trailing Symlink - {e}")
            else:
                logger.debug(
                    "Not creating trailing symlink, Docker environment")

            return moved_file

        return None

    async def handle_rename(self, entry: Entry) -> Optional[Path]:
        """
        Handles the rename for a downloaded entry.
        Returns the new pathlib.Path of the renamed file.

        Parameters
        ----------
        entry: Entry
            The downloaded entry.

        Returns
        -------
        Optional[pathlib.Path]
            The new path of the renamed file.
        """
        if entry.file_path is None:
            # This can't really happen but it's probably best to check
            # just in case the download client returns an incorrect fp.
            logger.error("entry.file_path is None?")
            return None

        async with self.app.acquire_db() as con:
            await con.execute("""
                SELECT
                    title,
                    desired_format,
                    season,
                    episode_offset
                FROM
                    shows
                WHERE id=?;
            """, entry.show_id)
            show_info = await con.fetchone()

        if show_info["desired_format"]:
            file_fmt = show_info["desired_format"]
        else:
            file_fmt = "{n} - {s00e00}"

        suffix = entry.file_path.suffix

        episode = str(entry.episode + show_info["episode_offset"])

        expressions = self.get_expression_mapping(
            show_info["title"],
            str(show_info["season"]),
            episode,
            ext=suffix
        )
        name = file_fmt.format_map(expressions)

        try:
            new_path = entry.file_path.with_name(name + suffix)
            await aiofiles.os.rename(entry.file_path, new_path)
        except PermissionError:
            logger.error("Error Renaming Release - Invalid Permissions")
        except Exception as e:
            logger.error(f"Error Renaming Release - {e}")
        else:
            return new_path

        return None

    def resolve_file(self, root: Path, episode: int) -> Optional[Path]:
        """
        Searches a directory tree for a specific episode
        file.

        If the passed path is a file, return it.

        Parameters
        ----------
        path: Path
            The directory.
        episode: int
            The episode to search for.

        Returns
        -------
        Optional[Path]
            The found Path. It is a file.
        """
        if root.is_file():
            return root

        root.resolve()
        for subpath in root.rglob("*"):
            try:
                parsed = anitopy.parse(subpath.name)
            except Exception:
                logger.debug(
                    f"anitopy - Could not parse '{subpath.name}', skipping")
                continue

            try:
                found = int(parsed["episode_number"])
            except (KeyError, ValueError, TypeError):
                continue
            if found == episode:
                return subpath

        return None

    async def check_show_entry(self, entry: Entry) -> None:
        """
        Checks a specific show entry for download completion.
        If an entry is completed, send it to renaming and moving.

        Parameters
        ----------
        entry: Entry
            The object of the entry in the database.
        """
        logger.info(f"Checking Release Status - {entry}")

        # Initial downloading check. This conditional branch is essentially
        # waiting for the downloaded file to appear in the file system.
        if entry.state == EntryState.downloading:
            path = await self.app.dl_client.get_torrent_fp(entry.torrent_hash)
            if not path:
                show_id = entry.show_id
                episode = entry.episode
                logger.error(f"Show Entry with ID {show_id} Episode {episode} missing from download client.")
                return
            elif not path.parent.is_dir():
                logger.error(f"'{path}' could not be read")
                return

            await entry.set_path(path)
        else:
            path = entry.file_path

        if path is None:
            return

        # Sometimes the file path may exist on disk, but it isn't fully
        # downloaded by the torrent client at this point in time.
        is_completed = await self.app.dl_client.check_torrent_completed(entry.torrent_hash)
        if not is_completed:
            logger.info(f"{entry} torrent state is not completed")
            return

        # This ensures that the path is an actual file rather than
        # a directory. Sometimes with torrents the files can be in
        # folders. Batch releases are typically always in folders.
        path = self.resolve_file(path, entry.episode)
        if path is None:
            return

        logger.info(f"Found Release to Process - {entry}")

        # These aren't elifs due to the fact that processing can
        # stop at any time and the ifs are actually used to continue
        # where processing left off when process resumes. There were
        # some other reasons that they aren't elifs that I discovered
        # while testing.
        if entry.state == EntryState.downloading:
            await entry.set_state(EntryState.downloaded)
            await entry.set_path(path)
            logger.info(f"Release Marked as Downloaded - {entry}")

        if entry.state == EntryState.downloaded:
            logger.info(f"Preparing to Rename Release - {entry}")
            renamed_path = await self.handle_rename(entry)
            if renamed_path is None:
                return

            await entry.set_state(EntryState.renamed)
            await entry.set_path(renamed_path)
            logger.info(f"Release Marked as Renamed - {entry}")

        if entry.state == EntryState.renamed:
            logger.info(f"Preparing to Move Release - {entry}")
            moved_path = await self.handle_move(entry)
            if moved_path is None:
                return

            await entry.set_state(EntryState.moved)
            await entry.set_path(moved_path)
            logger.info(f"Release Marked as Moved - {entry}")

        await entry.set_state(EntryState.completed)
        logger.info(f"Release Marked as Completed - {entry}")

    async def check_show_entries(self) -> None:
        """
        Queries the database for show entries marked as
        downloading, then passes them to a separate function
        to check for completion.
        """
        async with self.app.acquire_db() as con:
            await con.execute("""
                SELECT
                    id,
                    show_id,
                    episode,
                    torrent_hash,
                    current_state,
                    file_path,
                    last_update
                FROM
                    show_entry
                WHERE current_state != 'completed';
            """)
            entries = await con.fetchall()

        for entry in entries:
            entry = Entry(self.app, entry)
            await self.check_show_entry(entry)
