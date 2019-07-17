import asyncio

from quart.ctx import AppContext


class Downloader:
    def __init__(self, app_context: AppContext):
        self.app = app_context.app


    async def start(self):
        while True:
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
