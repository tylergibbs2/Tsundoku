from __future__ import annotations
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

    def __init__(self, app: AppContext):
        self._app = app


    @classmethod
    def from_dict(cls, app: AppContext, _from: dict) -> SearchResult:
        """
        Returns a valid SearchResult object from a data dict.

        Parameters
        ----------
        app: AppContext
            The Quart app.
        from: dict
            The data dict.

        Returns
        -------
        SearchResult:
            Result.
        """
        instance = cls(app)

        instance.title = _from.pop("title")

        unparsed_date = _from.pop("published")

        instance.published = datetime.datetime.strptime(unparsed_date, "%a, %d %b %Y %H:%M:%S %z")
        instance.torrent_link = _from.pop("link")
        instance.post_link = _from.pop("id")
        instance.size = _from.pop("nyaa_size")

        instance.seeders = int(_from.pop("nyaa_seeders"))
        instance.leechers = int(_from.pop("nyaa_leechers"))

        instance.show_id = None

        return instance


    @classmethod
    def from_necessary(cls, app: AppContext, show_id: int, torrent_link: str) -> SearchResult:
        """
        Returns a SearchResult object that is capable of
        running the `process` method, and has no other attributes.

        Parameters
        ----------
        app: AppContext
            The Quart app.
        show_id: int
            The ID of the show to be added to.
        torrent_link: str
            The link to the .torrent file.

        Returns
        -------
        SearchResult:
            Result for processing.
        """


    def to_dict(self) -> dict:
        return {
            "show_id": self.show_id,
            "title": self.title,
            "published": self.published.strftime("%d %b %Y"),
            "torrent_link": self.torrent_link,
            "post_link": self.post_link,
            "size": self.size,
            "seeders": self.seeders,
            "leechers": self.leechers
        }


    async def get_episodes(self) -> List[int]:
        """
        Returns a list of episodes that are contained
        within the torrent.

        Returns
        -------
        List[int]:
            List of episodes.
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
        Processes a SearchResult for downloading.

        Returns
        -------
        List[Entry]:
            Returns a list of added entries.
        """
        added = []

        if self.show_id is None:
            logger.error("Nyaa - Unable to process result without `show_id` set.")
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
    @staticmethod
    def _get_query_url(query: str) -> None:
        """
        Sets the query for searching nyaa.si.

        Parameters
        ----------
        query: str
            The search query.
        """
        return "https://nyaa.si/?page=rss&c=1_2&s=seeders&o=desc&q=" + quote_plus(query)

    @staticmethod
    async def search(app: AppContext, query: str) -> List[SearchResult]:
        """
        Searches for a query on nyaa.si.

        Parameters
        ----------
        query: str
            The search query.
        """
        url = NyaaSearcher._get_query_url(query)
        loop = asyncio.get_running_loop()

        feed = await loop.run_in_executor(None, feedparser.parse, url)
        found = []
        for item in feed["entries"]:
            try:
                anitopy.parse(item["title"])
            except Exception as e:
                logger.warn(f"Anitopy - Could not Parse '{item['title']}', skipping")
                continue

            found.append(SearchResult.from_dict(app, item))

        return found
