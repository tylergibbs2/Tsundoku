import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

import aiofiles.os

from tsundoku.config import FeedsConfig, GeneralConfig
from tsundoku.manager import Entry, EntryState, Library
from tsundoku.utils import ExprDict, move, parse_anime_title

logger = logging.getLogger("tsundoku")


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

    app: "TsundokuApp"

    complete_check: int
    seed_ratio_limit: float

    default_desired_format: str
    use_season_folder: bool

    def __init__(self, app_context: Any) -> None:
        self.app = app_context.app

    async def update_config(self) -> None:
        """
        Updates the configuration for the task.
        """
        feed_cfg = await FeedsConfig.retrieve(self.app)
        self.complete_check = feed_cfg.complete_check_interval
        self.seed_ratio_limit = feed_cfg.seed_ratio_limit

        general_cfg = await GeneralConfig.retrieve(self.app)
        self.default_desired_format = general_cfg.default_desired_format
        self.use_season_folder = general_cfg.use_season_folder

    async def start(self) -> None:
        logger.debug("Downloader task started.")

        while True:
            await self.update_config()

            try:
                await self.check_show_entries()
            except Exception as e:
                import traceback

                traceback.print_exc()
                logger.error(f"Error occurred while checking show entries, '{e}'", exc_info=True)

            await asyncio.sleep(self.complete_check)

    def get_expression_mapping(self, title: str, season: str, episode: str, version: str, **kwargs: str) -> ExprDict:
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
            name=title,
            title=title,
            s=season,
            season=season,
            e=episode,
            episode=episode,
            s00=season.zfill(2),
            e00=episode.zfill(2),
            s00e00=f"s{season.zfill(2)}e{episode.zfill(2)}",
            S00E00=f"S{season.zfill(2)}E{episode.zfill(2)}",
            sxe=f"{season}x{episode.zfill(2)}",
            version=version,
            v=version,
            **kwargs,
        )

    async def begin_handling(
        self,
        show_id: int,
        episode: int,
        magnet_url: str,
        version: str,
        manual: bool = False,
    ) -> int | None:
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
        version: str
            The version of the release.

        Returns
        -------
        Optional[int]:
            The ID of the added entry.
        """
        try:
            torrent_hash = await self.app.dl_client.add_torrent(magnet_url)
        except Exception as e:
            logger.exception(f"Failed to begin handling, could not connect to download client: {e}")
            self.app.flags.DL_CLIENT_CONNECTION_ERROR = True
            return None

        self.app.flags.DL_CLIENT_CONNECTION_ERROR = False

        if torrent_hash is None:
            logger.warning(f"Failed to add Magnet URL {magnet_url} to download client")
            return None

        # TODO: handle entry insertion in the Entry class
        async with self.app.acquire_db() as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    INSERT OR REPLACE INTO
                        show_entry (
                            show_id,
                            episode,
                            version,
                            torrent_hash,
                            created_manually
                        )
                    VALUES
                        (:show_id, :episode, :version, :torrent_hash, :manual);
                """,
                    {
                        "show_id": show_id,
                        "episode": episode,
                        "version": version,
                        "torrent_hash": torrent_hash,
                        "manual": manual,
                    },
                )
                await cur.execute(
                    """
                    SELECT
                        id,
                        show_id,
                        episode,
                        version,
                        current_state,
                        torrent_hash,
                        file_path,
                        created_manually,
                        last_update
                    FROM
                        show_entry
                    WHERE
                        id = ?;
                """,
                    cur.lastrowid,
                )
                entry = await cur.fetchone()

        entry = Entry(self.app, entry)
        await entry.set_state(EntryState.downloading)

        logger.info(f"Release Marked as Downloading - <e{entry.id}>")

        return entry.id

    async def handle_move(self, entry: Entry) -> Path | None:
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
            logger.error(f"<e{entry.id}> file path is None?")
            return None

        async with self.app.acquire_db() as con:
            show_info = await con.fetchone(
                """
                SELECT
                    library_id,
                    title,
                    title_local,
                    season
                FROM
                    shows
                WHERE id=?;
            """,
                entry.show_id,
            )

        season = str(show_info["season"])
        title = show_info["title_local"] if show_info["title_local"] is not None else show_info["title"]

        library: Library = await Library.from_id(self.app, show_info["library_id"])
        desired_folder = library.folder / title
        if self.use_season_folder:
            desired_folder /= f"Season {season}"

        desired_folder.mkdir(parents=True, exist_ok=True)

        name = entry.file_path.name
        desired_path = desired_folder / name

        try:
            await move(str(entry.file_path), str(desired_path))
        except PermissionError:
            logger.error(f"Error Moving Release <e{entry.id}> - Invalid Permissions")
        except Exception as e:
            logger.error(f"Error Moving Release <e{entry.id}> - {e}", exc_info=True)
        else:
            try:
                entry.file_path.symlink_to(desired_path)
            except Exception as e:
                logger.warning(f"Failed to Create Trailing Symlink - {e}", exc_info=True)

            return desired_path

        return None

    async def handle_rename(self, entry: Entry) -> Path | None:
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
            logger.error(f"<e{entry.id}> file_path is None?")
            return None

        async with self.app.acquire_db() as con:
            show_info = await con.fetchone(
                """
                SELECT
                    title,
                    title_local,
                    desired_format,
                    season,
                    episode_offset
                FROM
                    shows
                WHERE id=?;
            """,
                entry.show_id,
            )

        if show_info["desired_format"]:
            file_fmt = show_info["desired_format"]
        else:
            file_fmt = self.default_desired_format

        suffix = entry.file_path.suffix

        title = show_info["title_local"] if show_info["title_local"] is not None else show_info["title"]
        episode = str(entry.episode + show_info["episode_offset"])

        expressions = self.get_expression_mapping(
            title,
            str(show_info["season"]),
            episode,
            entry.version,
            ext=suffix,
        )
        name = file_fmt.format_map(expressions)

        try:
            new_path = entry.file_path.with_name(name + suffix)
            await aiofiles.os.rename(entry.file_path, new_path)
        except PermissionError:
            logger.error(f"Error Renaming Release <e{entry.id}> - Invalid Permissions")
        except Exception as e:
            logger.error(f"Error Renaming Release <e{entry.id}> - {e}", exc_info=True)
        else:
            return new_path

        return None

    def resolve_file(self, root: Path, episode: int) -> Path | None:
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
                parsed = parse_anime_title(subpath.name)
            except Exception:
                logger.error(
                    f"Anitopy - Could not parse `{subpath.name}`, skipping",
                    exc_info=True,
                )
                continue  # TODO: maybe ask user on UI to match manually

            if parsed is None or "episode_number" not in parsed:
                continue

            if not isinstance(parsed["episode_number"], str) or not parsed["episode_number"].isdigit():
                continue

            found = int(parsed["episode_number"])
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
        logger.info(f"Checking Release Status - <e{entry.id}>")

        if entry.state == EntryState.failed:
            return

        # Sometimes the file path may exist on disk, but it isn't fully
        # downloaded by the torrent client at this point in time.
        is_completed = await self.app.dl_client.check_torrent_completed(entry.torrent_hash)
        if not is_completed:
            logger.info(f"<e{entry.id}> torrent state is not completed")
            return

        # Initial downloading check. This conditional branch is essentially
        # waiting for the downloaded file to appear in the file system.
        if entry.state == EntryState.downloading:
            path = await self.app.dl_client.get_torrent_fp(entry.torrent_hash)
            if not path:
                logger.error(f"Entry <e{entry.id}> missing from download client, marking as failed.")
                await entry.set_state(EntryState.failed)
                return
            if not path.parent.is_dir():
                logger.error(f"<e{entry.id}>, `{path}` could not be read")
                return

            await entry.set_path(path)
        else:
            path = entry.file_path

        if path is None:
            return

        # This ensures that the path is an actual file rather than
        # a directory. Sometimes with torrents the files can be in
        # folders. Batch releases are typically always in folders.
        path = self.resolve_file(path, entry.episode)
        if path is None:
            return

        logger.info(f"Found Release to Process - <e{entry.id}>")

        # These aren't elifs due to the fact that processing can
        # stop at any time and the ifs are actually used to continue
        # where processing left off when process resumes. There were
        # some other reasons that they aren't elifs that I discovered
        # while testing.
        if entry.state == EntryState.downloading:
            await entry.set_state(EntryState.downloaded)
            await entry.set_path(path)
            logger.info(f"Release Marked as Downloaded - <e{entry.id}>")

        if entry.state == EntryState.downloaded:
            seed_ratio = await self.app.dl_client.check_torrent_ratio(entry.torrent_hash)
            if seed_ratio is None:
                logger.error(f"<e{entry.id}> seed ratio could not be determined")
                return
            if seed_ratio < self.seed_ratio_limit:
                logger.info(f"<e{entry.id}> seed ratio is below limit ({self.seed_ratio_limit})")
                return

            logger.info(f"Preparing to Rename Release - <e{entry.id}>")
            renamed_path = await self.handle_rename(entry)
            if renamed_path is None:
                await entry.set_state(EntryState.failed)
                return

            await entry.set_state(EntryState.renamed)
            await entry.set_path(renamed_path)
            logger.info(f"Release Marked as Renamed - <e{entry.id}>")

        async with self.app.acquire_db() as con:
            library_id = await con.fetchval(
                """
                SELECT
                    library_id
                FROM
                    shows
                WHERE id=?;
            """,
                entry.show_id,
            )

        if library_id is None:
            logger.error(f"Show <s{entry.show_id}> is missing a library. Cannot process entry <e{entry.id}>")
            return

        if entry.state == EntryState.renamed:
            logger.info(f"Preparing to Move Release - <e{entry.id}>")
            moved_path = await self.handle_move(entry)
            if moved_path is None:
                await entry.set_state(EntryState.failed)
                return

            await entry.set_state(EntryState.moved)
            await entry.set_path(moved_path)
            logger.info(f"Release Marked as Moved - <e{entry.id}>")

        await entry.set_state(EntryState.completed)
        logger.info(f"Release Marked as Completed - <e{entry.id}>")

    async def check_show_entries(self) -> None:
        """
        Queries the database for show entries marked as
        downloading, then passes them to a separate function
        to check for completion.
        """
        async with self.app.acquire_db() as con:
            entries = await con.fetchall(
                """
                SELECT
                    id,
                    show_id,
                    episode,
                    version,
                    torrent_hash,
                    current_state,
                    file_path,
                    created_manually,
                    last_update
                FROM
                    show_entry
                WHERE
                    current_state != 'completed'
                    AND current_state != 'failed';
            """
            )

        for entry in entries:
            entry = Entry(self.app, entry)
            await self.check_show_entry(entry)
