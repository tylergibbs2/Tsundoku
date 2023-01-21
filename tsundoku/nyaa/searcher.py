from __future__ import annotations

import asyncio
import datetime
import logging
from typing import List, Optional, TYPE_CHECKING
from urllib.parse import quote_plus

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

    app: TsundokuApp

import feedparser

from tsundoku.manager import Entry, EntryState
from tsundoku.utils import parse_anime_title

logger = logging.getLogger("tsundoku")


class SearchResult:
    show_id: Optional[int]

    title: str

    published: datetime.datetime
    torrent_link: str
    post_link: str
    size: str

    seeders: int
    leechers: int

    def __init__(self, app: TsundokuApp) -> None:
        self._app = app

    @classmethod
    def from_dict(cls, app: TsundokuApp, _from: dict) -> SearchResult:
        """
        Returns a valid SearchResult object from a data dict.

        Parameters
        ----------
        app: TsundokuApp
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

        instance.published = datetime.datetime.strptime(
            unparsed_date, "%a, %d %b %Y %H:%M:%S %z"
        )
        instance.torrent_link = _from.pop("link")
        instance.post_link = _from.pop("id")
        instance.size = _from.pop("nyaa_size")

        instance.seeders = int(_from.pop("nyaa_seeders"))
        instance.leechers = int(_from.pop("nyaa_leechers"))

        instance.show_id = None

        return instance

    @classmethod
    def from_necessary(
        cls, app: TsundokuApp, show_id: int, torrent_link: str
    ) -> SearchResult:
        """
        Returns a SearchResult object that is capable of
        running the `process` method, and has no other attributes.

        Parameters
        ----------
        app: TsundokuApp
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
        instance = cls(app)

        instance.show_id = show_id
        instance.torrent_link = torrent_link

        return instance

    def to_dict(self) -> dict:
        return {
            "show_id": self.show_id,
            "title": self.title,
            "published": self.published.strftime("%d %b %Y"),
            "torrent_link": self.torrent_link,
            "post_link": self.post_link,
            "size": self.size,
            "seeders": self.seeders,
            "leechers": self.leechers,
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
                parsed = parse_anime_title(file)
            except Exception:
                logger.error(
                    f"Anitopy - Could not Parse `{file}`, skipping", exc_info=True
                )
                continue

            if (
                parsed is None
                or "anime_type" in parsed
                or "episode_number" not in parsed
            ):
                continue

            if (
                not isinstance(parsed["episode_number"], str)
                or not parsed["episode_number"].isdigit()
            ):
                continue

            episodes.append(int(parsed["episode_number"]))

        return episodes

    async def process(self, overwrite: bool = False) -> List[Entry]:
        """
        Processes a SearchResult for downloading.

        Parameters
        ----------
        overwrite: bool
            Whether or not to overwrite existing
            entries in the database.

        Returns
        -------
        List[Entry]:
            Returns a list of added entries.
        """
        added: List[Entry] = []

        if self.show_id is None:
            logger.error("Nyaa - Unable to process result without `show_id` set.")
            return added

        episodes_to_process = []
        existing_torrents = set()
        async with self._app.acquire_db() as con:
            for episode in await self.get_episodes():
                exists = await con.fetchval(
                    """
                    SELECT
                        torrent_hash
                    FROM
                        show_entry
                    WHERE
                        show_id=?
                    AND
                        episode=?;
                """,
                    self.show_id,
                    episode,
                )
                if exists and overwrite:
                    existing_torrents.add(exists)
                    episodes_to_process.append(episode)
                elif not exists:
                    episodes_to_process.append(episode)

        if not episodes_to_process:
            return added

        if overwrite:
            async with self._app.acquire_db() as con:
                for hash_ in existing_torrents:
                    await con.execute(
                        """
                        DELETE FROM
                            show_entry
                        WHERE
                            torrent_hash=?;
                    """,
                        hash_,
                    )
                    await self._app.dl_client.delete_torrent(hash_)

        magnet = await self._app.dl_client.get_magnet(self.torrent_link)
        torrent_hash = await self._app.dl_client.add_torrent(magnet)

        if torrent_hash is None:
            logger.warning(f"Failed to add Magnet URL {magnet} to download client")
            return added

        async with self._app.acquire_db() as con:
            async with con.cursor() as cur:
                for episode in episodes_to_process:
                    await cur.execute(
                        """
                        INSERT INTO
                            show_entry
                            (show_id, episode, torrent_hash, created_manually)
                        VALUES
                            (?, ?, ?, ?);
                    """,
                        self.show_id,
                        episode,
                        torrent_hash,
                        True,
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
                        WHERE id = ?;
                    """,
                        cur.lastrowid,
                    )
                    entry = await cur.fetchone()

                    entry = Entry(self._app, entry)
                    await entry.set_state(EntryState.downloading)
                    added.append(entry)

        return added


class NyaaSearcher:
    @staticmethod
    def _get_query_url(query: str) -> str:
        """
        Sets the query for searching nyaa.si.

        Parameters
        ----------
        query: str
            The search query.
        """
        return "https://nyaa.si/?page=rss&c=1_2&s=seeders&o=desc&q=" + quote_plus(query)

    @staticmethod
    async def search(app: TsundokuApp, query: str) -> List[SearchResult]:
        """
        Searches for a query on nyaa.si.

        Parameters
        ----------
        app: TsundokuApp
            The app.
        query: str
            The search query.
        """
        url = NyaaSearcher._get_query_url(query)
        loop = asyncio.get_running_loop()

        feed = await loop.run_in_executor(None, feedparser.parse, url)
        found = []
        for item in feed["entries"]:
            try:
                parse_anime_title(item["title"])
            except Exception:
                logger.error(
                    f"Anitopy - Could not Parse `{item['title']}`, skipping",
                    exc_info=True,
                )
                continue

            found.append(SearchResult.from_dict(app, item))

        return found
