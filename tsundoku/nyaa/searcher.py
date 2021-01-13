import asyncio
import logging
from typing import List, Tuple
from urllib.parse import quote_plus

import anitopy
import feedparser
from quart.ctx import AppContext

from tsundoku.feeds.entry import Entry


logger = logging.getLogger("tsundoku")


class NyaaSearcher:
    def __init__(self, app: AppContext):
        self._base_url = "https://nyaa.si/?page=rss&c=1_2&s=seeders&o=desc&q="
        self.url = self._base_url

        self._app = app
        self._loop = asyncio.get_running_loop()

    def _set_query(self, query: str) -> None:
        """
        Sets the query for searching nyaa.si.

        Parameters
        ----------
        query: str
            The search query.
        """
        self.url = self._base_url + quote_plus(query)

    def check_release(self, parsed: dict) -> bool:
        """
        Checks if a release is desired.
        """
        if "batch" not in parsed.get("release_information", "").lower():
            return False
        elif parsed.get("video_resolution") and parsed["video_resolution"] != "1080p":
            return False

        return True


    async def get_episodes(self, link: str) -> List[int]:
        """
        Returns a list of episodes that are contained
        within the torrent.

        The return tuple is (episode, file_name)
        """
        files = await self._app.dl_client.get_file_structure(link)
        episodes = []
        for file in files:
            parsed = anitopy.parse(file)

            if "anime_type" in parsed.keys():
                continue

            try:
                episodes.append(int(parsed["episode_number"]))
            except (KeyError, ValueError, TypeError):
                pass

        return episodes


    async def search(self, show_id: int) -> List[Tuple[int, int]]:
        """
        Searches for a query on nyaa.si.

        Parameters
        ----------
        show_id: int
            The show to search for.
        """
        async with self._app.db_pool.acquire() as con:
            title = await con.fetchval("""
                SELECT
                    title
                FROM
                    shows
                WHERE
                id=$1;
            """, show_id)

        self._set_query(title)

        feed = await self._loop.run_in_executor(None, feedparser.parse, self.url)
        found = None
        for item in feed["entries"]:
            parsed = anitopy.parse(item["title"])
            if not self.check_release(parsed):
                continue

            found = item
            found["episodes"] = await self.get_episodes(item["link"])
            break

        if not found or not found["episodes"]:
            return []

        magnet = await self._app.dl_client.get_magnet(found["link"])
        torrent_hash = await self._app.dl_client.add_torrent(magnet)

        added = []

        if torrent_hash is None:
            logger.warn(f"Failed to add Magnet URL {magnet} to download client")
            return added

        for episode in found["episodes"]:
            async with self._app.db_pool.acquire() as con:
                exists = await con.fetchval("""
                    SELECT
                        episode
                    FROM
                        show_entry
                    WHERE
                        show_id=$1
                    AND
                        episode=$2;
                """, show_id, episode)
                if exists:
                    continue

                entry = await con.fetchrow("""
                INSERT INTO
                    show_entry
                    (show_id, episode, torrent_hash)
                VALUES
                    ($1, $2, $3, $4)
                RETURNING id, show_id, episode, current_state, torrent_hash;
                """, show_id, episode, torrent_hash)

            entry = Entry(self._app, entry)
            await entry.set_state("downloading")
            added.append((show_id, entry.episode))

        return added
