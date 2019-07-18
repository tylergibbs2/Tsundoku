import asyncio
import os
from pathlib import Path
import re
import shutil

from asyncpg import Record
from quart.ctx import AppContext

from feeds.exceptions import EntryNotInDeluge, SavePathDoesNotExist


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

    
    async def begin_handling(self, show_id: int, episode: int, magnet_url: str) -> None:
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
        """
        torrent_hash = await self.app.deluge.add_torrent(magnet_url)

        async with self.app.db_pool.acquire() as con:
            await con.execute("""
                INSERT INTO show_entry (show_id, episode, torrent_hash) VALUES ($1, $2, $3);
            """, show_id, episode, torrent_hash)

        
    async def mark_entry_complete(self, entry: Record) -> None:
        """
        Marks an entry as `complete` in the `show_entry` table.

        Parameters
        ----------
        entry: asyncpg.Record
            The entry to mark as complete.
        """
        async with self.app.db_pool.acquire() as con:
            await con.execute("""
                UPDATE show_entry SET current_state='complete' WHERE id=$1
            """, entry["id"])


    async def handle_move(self, entry: Record, target: Path) -> Path:
        """
        Handles the move for a downloaded entry.
        Returns the new pathlib.Path of the moved file.

        Parameters
        ----------
        entry: asyncpg.Record
            The downloaded entry.
        target: pathlib.Path
            The downloaded entry to be moved.

        Returns
        -------
        pathlib.Path
            The new path of the moved file.
        """
        async with self.app.db_pool.acquire() as con:
            show_info = await con.fetchrow("""
                SELECT desired_folder FROM shows WHERE id=$1;
            """, entry["show_id"])

        desired_folder = show_info["desired_folder"]
        if desired_folder is None:
            desired_folder = target.parent
        else:
            Path(desired_folder).mkdir(parents=True, exist_ok=True)
            desired_folder = Path(desired_folder)

        shutil.move(str(target), str(desired_folder))

        return desired_folder / target.name


    async def handle_rename(self, entry: Record, path: Path) -> Path:
        """
        Handles the rename for a downloaded entry.
        Returns the new pathlib.Path of the renamed file.

        Parameters
        ----------
        entry: asyncpg.Record
            The downloaded entry.
        path: pathlib.Path
            The path of the downloaded file.
        
        Returns
        -------
        pathlib.Path
            The new path of the renamed file.
        """
        suffix = path.suffix

        async with self.app.db_pool.acquire() as con:
            show_info = await con.fetchrow("""
                SELECT search_title, desired_format, season, episode_offset FROM shows WHERE id=$1;
            """, entry["show_id"])

        if show_info["desired_format"]:
            file_fmt = show_info["desired_format"]
        else:
            file_fmt = "{n} - {s00e00}"

        def formatting_re(match: re.Match):
            expression = match.group(1)

            season = str(show_info["season"])
            episode = str(entry["episode"] + show_info["episode_offset"])

            format_exprs = {
                "n": show_info["search_title"],
                "s": season,
                "e": episode,
                "s00": season.zfill(2),
                "e00": episode.zfill(2),
                "s00e00": f"S{season.zfill(2)}E{episode.zfill(2)}",
                "sxe": f"{season}x{episode.zfill(2)}"
            }

            return format_exprs.get(expression, expression)
        
        name = re.sub(r"{(\w+)}", formatting_re, file_fmt)

        new_path = path.with_name(name + suffix)
        os.rename(path, new_path)

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
            raise SavePathDoesNotExist(f"'{file_location}' could not be read")

        return location / file_name


    async def check_show_entry(self, entry: Record) -> None:
        """
        Checks a specific show entry for download completion.
        If an entry is completed, send it to renaming and moving.

        Parameters
        ----------
        entry: asyncpg.Record
            The record object of the entry in the database.
        """
        try:
            deluge_info = await self.app.deluge.get_torrent(entry["torrent_hash"], ["name", "move_completed_path"])
        except IndexError:
            show_id = entry["show_id"]
            episode = entry["episode"]
            raise EntryNotInDeluge(f"Show Entry with ID {show_id} Episode {episode} missing from Deluge.")

        file_location = deluge_info["move_completed_path"]
        file_name = deluge_info["name"]
        
        path = self.get_file_path(file_location, file_name)
        if not path.is_file():
            return

        renamed_path = await self.handle_rename(entry, path)
        moved_path = await self.handle_move(entry, renamed_path)

        await self.mark_entry_complete(entry)

        print(moved_path)

    
    async def check_show_entries(self) -> None:
        """
        Queries the database for show entries marked as
        downloading, then passes them to a separate function
        to check for completion.
        """
        async with self.app.db_pool.acquire() as con:
            entries = await con.fetch("""
                SELECT id, show_id, episode, torrent_hash FROM show_entry
                WHERE current_state = 'downloading';
            """)

        for entry in entries:
            await self.check_show_entry(entry)
