import asyncio
import datetime
import logging
from typing import List
from urllib.parse import quote_plus

import anitopy
import feedparser
from quart.ctx import AppContext

from tsundoku.feeds.entry import Entry


logger = logging.getLogger("tsundoku")


class SearchResult:
    show_id: int

    title: str

    published: datetime.datetime
    torrent_link: str
    post_link: str
    size: str

    seeders: int
    leechers: int

    def __init__(self, app: AppContext, feed_item: dict):
        self._app = app

        self.title = feed_item.pop("title")

        unparsed_date = feed_item.pop("published")

        self.published = datetime.datetime.strptime(unparsed_date, "%a, %d %b %Y %H:%M:%S %z")
        self.torrent_link = feed_item.pop("link")
        self.post_link = feed_item.pop("id")
        self.size = feed_item.pop("nyaa_size")

        self.seeders = int(feed_item.pop("nyaa_seeders"))
        self.leechers = int(feed_item.pop("nyaa_leechers"))

        self.show_id = None

    async def get_episodes(self) -> List[int]:
        """
        Returns a list of episodes that are contained
        within the torrent.
        """
        files = await self._app.dl_client.get_file_structure(self.torrent_link)
        episodes = []
        for file in files:
            try:
                parsed = anitopy.parse(file)
            except Exception as e:
                logger.warn(f"anitopy - Could not Parse '{file}', skipping")
                continue

            if "anime_type" in parsed.keys():
                continue

            try:
                episodes.append(int(parsed["episode_number"]))
            except (KeyError, ValueError, TypeError):
                pass

        return episodes

    async def process(self) -> List[Entry]:
        """
        Processes a search result for downloading.

        Returns
        -------
        List[Entry]:
            Returns a list of added entries.
        """
        added = []

        if self.show_id is None:
            logger.error("nyaa - Unable to process result without show_id set.")
            return added

        magnet = await self._app.dl_client.get_magnet(self.torrent_link)
        torrent_hash = await self._app.dl_client.add_torrent(magnet)

        if torrent_hash is None:
            logger.warn(f"Failed to add Magnet URL {magnet} to download client")
            return added

        for episode in await self.get_episodes():
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
                """, self.show_id, episode)
                if exists:
                    continue

                entry = await con.fetchrow("""
                INSERT INTO
                    show_entry
                    (show_id, episode, torrent_hash)
                VALUES
                    ($1, $2, $3)
                RETURNING id, show_id, episode, current_state, torrent_hash, file_path;
                """, self.show_id, episode, torrent_hash)

            entry = Entry(self._app, entry)
            await entry.set_state("downloading")
            added.append(Entry)

        return added


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


    async def search(self, query: str) -> List[SearchResult]:
        """
        Searches for a query on nyaa.si.

        Parameters
        ----------
        query: str
            The search query.
        """
        self._set_query(query)

        feed = await self._loop.run_in_executor(None, feedparser.parse, self.url)
        found = []
        for item in feed["entries"]:
            try:
                parsed = anitopy.parse(item["title"])
            except Exception as e:
                logger.warn(f"anitopy - Could not Parse '{item['title']}', skipping")
                continue

            found.append(SearchResult(self._app, item))

        return found
