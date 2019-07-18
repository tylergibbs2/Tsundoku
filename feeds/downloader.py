import asyncio
from pathlib import Path

from asyncpg import Record
from quart.ctx import AppContext

from feeds.exceptions import EntryNotInDeluge, SavePathDoesNotExist


class Downloader:
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


    def is_downloaded(self, file_location: str, file_name: str) -> bool:
        """
        Detects whether a file at a designated path
        is downloaded.

        Parameters
        ----------
        file_location: str
            The file's location.
        file_name: str
            The name of the file at the location.

        Returns
        -------
        bool
            True if the file is downloaded, False otherwise.
        """
        file_location = file_location.replace("\\", "/")
        location = Path(file_location)
        if not location.is_dir():
            raise SavePathDoesNotExist(f"'{file_location}' could not be read")

        file_path = Path(f"{file_location}/{file_name}")

        return file_path.is_file()


    async def check_show_entry(self, entry: Record) -> None:
        """
        Checks a specific show entry for download completion.
        If an entry is completed, send it to renaming and moving.

        Parameters
        ----------
        entry: asyncpg.Record
            The record object of the entry in the database.
        """
        deluge_info = await self.app.deluge.get_torrent(entry["torrent_hash"])

        if not deluge_info:
            show_id = entry["show_id"]
            episode = entry["episode"]
            raise EntryNotInDeluge(f"Show Entry with ID {show_id} Episode {episode} missing from Deluge.")

        file_location = deluge_info["save_path"]
        file_name = deluge_info["name"]

        if not self.is_downloaded(file_location, file_name):
            return

        print("downloaded")

    
    async def check_show_entries(self) -> None:
        """
        Queries the database for show entries marked as
        downloading, then passes them to a separate function
        to check for completion.
        """
        async with self.app.db_pool.acquire() as con:
            entries = await con.fetch("""
                SELECT show_id, episode, torrent_hash FROM show_entry
                WHERE current_state = 'downloading';
            """)

        for entry in entries:
            await self.check_show_entry(entry)
