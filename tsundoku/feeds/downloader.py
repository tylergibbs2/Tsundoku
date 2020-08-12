import asyncio
import logging
import os
from pathlib import Path
import re
import shutil
from typing import Optional

from asyncpg import Record
from quart.ctx import AppContext

from tsundoku.feeds.entry import Entry
from tsundoku.feeds.exceptions import EntryNotInDeluge, FeedsError, SavePathDoesNotExist


logger = logging.getLogger("tsundoku")


class Downloader:
    """
    Begins handling by adding the torrent to Deluge
    and inserting a row into the `show_entry` table.

    The download manager will then check for the
    entry's completion periodically (15 seconds) until
    the item is found to be complete.

    A completed item, once found, will be renamed and then
    subsequently moved to a target destination.

    Finally, the item will be marked as complete in the
    `show_entry` table.
    """
    def __init__(self, app_context: AppContext):
        self.app = app_context.app


    async def start(self) -> None:
        while True:
            await self.check_show_entries()
            await asyncio.sleep(15)


    async def begin_handling(self, show_id: int, episode: int, magnet_url: str) -> int:
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
        int:
            The ID of the added entry.
        """
        torrent_hash = await self.app.deluge.add_torrent(magnet_url)

        if torrent_hash is None:
            logger.warn(f"Failed to add Magnet URL {magnet_url} to Deluge")
            raise FeedsError(f"Failed to add Magnet URL {magnet_url} to Deluge")

        async with self.app.db_pool.acquire() as con:
            entry_id = await con.fetchval("""
                INSERT INTO show_entry (show_id, episode, torrent_hash) VALUES ($1, $2, $3) RETURNING id;
            """, show_id, episode, torrent_hash)
        logger.info(f"Release Marked as Downloading - {show_id}, {episode}")

        return entry_id


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
            return

        async with self.app.db_pool.acquire() as con:
            show_info = await con.fetchrow("""
                SELECT title, desired_folder, episode_offset, season FROM shows WHERE id=$1;
            """, entry.show_id)

        def formatting_re(match: re.Match):
            expression = match.group(1)

            season = str(show_info["season"])
            episode = str(entry.episode + show_info["episode_offset"])

            format_exprs = {
                "n": show_info["title"],
                "s": season,
                "e": episode,
                "s00": season.zfill(2),
                "e00": episode.zfill(2),
                "s00e00": f"s{season.zfill(2)}e{episode.zfill(2)}",
                "S00E00": f"S{season.zfill(2)}E{episode.zfill(2)}",
                "sxe": f"{season}x{episode.zfill(2)}"
            }

            return format_exprs.get(expression, expression)

        desired_folder = show_info["desired_folder"]
        if desired_folder is None:
            desired_folder = entry.file_path.parent
        else:
            expressive_folder = re.sub(r"{(\w+)}", formatting_re, desired_folder)

            Path(expressive_folder).mkdir(parents=True, exist_ok=True)
            desired_folder = Path(expressive_folder)

        try:
            shutil.move(str(entry.file_path), str(desired_folder))
        except PermissionError:
            logger.error("Error Moving Release - Invalid Permissions")
        except Exception as e:
            logger.error(f"Error Moving Release - {e}")
        else:
            return desired_folder / entry.file_path.name


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
            logger.error("entry.file_path is None?")
            return

        suffix = entry.file_path.suffix

        async with self.app.db_pool.acquire() as con:
            show_info = await con.fetchrow("""
                SELECT title, desired_format, season, episode_offset FROM shows WHERE id=$1;
            """, entry.show_id)

        if show_info["desired_format"]:
            file_fmt = show_info["desired_format"]
        else:
            file_fmt = "{n} - {s00e00}"

        def formatting_re(match: re.Match):
            expression = match.group(1)

            season = str(show_info["season"])
            episode = str(entry.episode + show_info["episode_offset"])

            format_exprs = {
                "n": show_info["title"],
                "s": season,
                "e": episode,
                "s00": season.zfill(2),
                "e00": episode.zfill(2),
                "s00e00": f"s{season.zfill(2)}e{episode.zfill(2)}",
                "S00E00": f"S{season.zfill(2)}E{episode.zfill(2)}",
                "sxe": f"{season}x{episode.zfill(2)}"
            }

            return format_exprs.get(expression, expression)

        name = re.sub(r"{(\w+)}", formatting_re, file_fmt)

        new_path = entry.file_path.with_name(name + suffix)

        try:
            os.rename(entry.file_path, new_path)
        except PermissionError:
            logger.error("Error Renaming Release - Invalid Permissions")
        except Exception as e:
            logger.error(f"Error Renaming Release - {e}")
        else:
            return new_path


    def get_file_path(self, file_location: str, file_name: str) -> bool:
        """
        Calculates the path of the file given location and name.

        Parameters
        ----------
        file_location: str
            The file's location.
        file_name: str
            The name of the file at the location.

        Returns
        -------
        pathlib.Path
            The Path of the file.
        """
        file_location = file_location.replace("\\", "/")
        location = Path(file_location)
        if not location.is_dir():
            logger.error(f"'{file_location}' could not be read")
            raise SavePathDoesNotExist(f"'{file_location}' could not be read")

        return location / file_name


    async def check_show_entry(self, entry: Entry) -> None:
        """
        Checks a specific show entry for download completion.
        If an entry is completed, send it to renaming and moving.

        Parameters
        ----------
        entry: Entry
            The object of the entry in the database.
        """
        logger.info(f"Checking Release Status - {entry.show_id, entry.episode}")

        if entry.state == "downloading":
            try:
                deluge_info = await self.app.deluge.get_torrent(
                    entry.torrent_hash,
                    ["name", "move_completed_path"]
                )
            except IndexError:
                show_id = entry.show_id
                episode = entry.episode
                logger.error(f"Show Entry with ID {show_id} Episode {episode} missing from Deluge.")
                raise EntryNotInDeluge(f"Show Entry with ID {show_id} Episode {episode} missing from Deluge.")

            file_location = deluge_info["move_completed_path"]
            file_name = deluge_info["name"]

            path = self.get_file_path(file_location, file_name)
        else:
            path = entry.file_path

        if path is None or not path.is_file():
            return

        logger.info(f"Found Release to Process - {entry.show_id}, {entry.episode}, {entry.state}")

        if entry.state == "downloading":
            await entry.set_state("downloaded")
            await entry.set_path(path)
            logger.info(f"Release Marked as Downloaded - {entry.show_id}, {entry.episode}")

        if entry.state == "downloaded":
            renamed_path = await self.handle_rename(entry)
            if renamed_path is None:
                return

            await entry.set_state("renamed")
            await entry.set_path(renamed_path)
            logger.info(f"Release Marked as Renamed - {entry.show_id}, {entry.episode}")

        if entry.state == "renamed":
            moved_path = await self.handle_move(entry)
            if moved_path is None:
                return

            await entry.set_state("moved")
            await entry.set_path(moved_path)
            logger.info(f"Release Marked as Moved - {entry.show_id}, {entry.episode}")

        await entry.set_state("completed")
        logger.info(f"Release Marked as Completed - {entry.show_id}, {entry.episode}")


    async def check_show_entries(self) -> None:
        """
        Queries the database for show entries marked as
        downloading, then passes them to a separate function
        to check for completion.
        """
        async with self.app.db_pool.acquire() as con:
            entries = await con.fetch("""
                SELECT id, show_id, episode, torrent_hash, current_state, file_path FROM show_entry
                WHERE current_state != 'completed';
            """)

        for entry in entries:
            entry = Entry(self.app, entry)
            await self.check_show_entry(entry)
