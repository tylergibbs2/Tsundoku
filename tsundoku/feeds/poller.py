import asyncio
from dataclasses import dataclass
import logging
from typing import Optional, List, Tuple

import feedparser
from fuzzywuzzy import process
from quart.ctx import AppContext

from tsundoku.config import get_config_value
from tsundoku.nyaa import NyaaSearcher


logger = logging.getLogger("tsundoku")


@dataclass
class EntryMatch:
    """
    Represents a match between an RSS feed item
    and the app's local database.

    Attributes
    ----------
    passed_name: str
        The name initially passed to the matching function.
    matched_id: str
        The ID in the database that the passed name was matched with.
    match_percent: int
        The percent match the two names are on a scale of 0 to 100.
    """
    passed_name: str
    matched_id: int
    match_percent: int


class Poller:
    """
    The polling manager handles all RSS feed related
    activities.

    Once started, the manager will iterate through every
    enabled RSS feed parser and parse their respective
    feeds using custom logic defined in each parser.

    Items that are matched with the `shows` database will
    be then passed onto the download manager for downloading,
    renaming, and moving.
    """
    def __init__(self, app_context: AppContext):
        self.app = app_context.app
        self.loop = asyncio.get_running_loop()

        self.current_parser = None  # keeps track of the current RSS feed parser.
        self.nyaa = NyaaSearcher(self.app)

        interval = get_config_value("Tsundoku", "polling_interval")
        try:
            self.interval = int(interval)
        except ValueError:
            logger.error(f"'{interval}' is an invalid polling interval.")
            raise Exception(f"'{interval}' is an invalid polling interval.")


    async def start(self) -> None:
        """
        The program will poll every n seconds, as specified
        in the configuration file.
        """
        if not self.app.rss_parsers:
            logger.error("No RSS parsers found.")
            return

        while True:
            await self.poll()

            await asyncio.sleep(self.interval)


    async def poll(self) -> List[Tuple[int, int]]:
        """
        Iterates through every installed RSS parser
        and will check for new items to download.

        The order of the parsers used is determined
        by how they are listed in the configuration.

        Returns a list of releases found in the format
        (show_id, episode).
        """
        logger.info("Checking for New Releases...")

        self.app.seen_titles = set()

        found = []

        for parser in self.app.rss_parsers:
            self.current_parser = parser
            feed = await self.get_feed_from_parser()

            logger.info(f"{parser.name} - Checking for New Releases...")
            found += await self.check_feed(feed)
            logger.info(f"{parser.name} - Checked for New Releases")

        self.current_parser = None

        logger.info("Searching nyaa.si for New Releases")
        found += await self.check_nyaa()
        logger.info("Searched nyaa.si for New Releases")

        logger.info("Checked for New Releases")

        return found


    async def check_nyaa(self) -> List[Tuple[int, int]]:
        """
        Automatically searches nyaa.si for desired shows
        and will return a list of tuples in the format of
        (show_id, episode).
        """
        async with self.app.db_pool.acquire() as con:
            desired_shows = await con.fetch("""
                SELECT
                    id
                FROM
                    shows;
            """)

        found = []
        for show in desired_shows:
            found += await self.nyaa.search(show["id"])

        return found


    async def check_feed(self, feed: dict) -> List[Tuple[int, int]]:
        """
        Iterates through the list of items in an
        RSS feed and will individually check each
        item. Returns a list of tuples in the format
        (show_id, episode).

        Parameters
        ----------
        feed: dict
            The RSS feed.
        """
        found_items = []

        for item in feed["items"]:
            found = await self.check_item(item)
            if found:
                found_items.append(found)

        return found_items


    async def is_parsed(self, show_id: int, episode: int) -> bool:
        """
        Will check if a specified episode of a
        show has already been parsed.

        Parameters
        ----------
        show_id: int
            The ID of the show to check.
        episode: int
            The episode to check if it has been parsed.

        Returns
        -------
        bool
            True if the episode has been parsed, False otherwise.
        """
        async with self.app.db_pool.acquire() as con:
            show_entry = await con.fetchval("""
                SELECT
                    id
                FROM
                    show_entry
                WHERE show_id=$1 AND episode=$2;
            """, show_id, episode)

        return bool(show_entry)


    async def check_item_for_match(self, show_name: str, episode: int) -> Optional[EntryMatch]:
        """
        Takes a show name from RSS and an episode from RSS and
        checks if the object should be downloaded.

        An item should be downloaded only if it is in the
        `shows` table and the episode is not already in the
        `show_entry` table.

        Parameters
        ----------
        show_name: str
            The name of the show from RSS.
        episode: int
            The episode of the entry from RSS.

        Returns
        -------
        Optional[EntryMatch]
            The EntryMatch for the passed show name.
            Could be None if no shows are desired.
        """
        async with self.app.db_pool.acquire() as con:
            desired_shows = await con.fetch("""
                SELECT
                    id,
                    title
                FROM
                    shows;
            """)
        show_list = {show["title"]: show["id"] for show in desired_shows}

        if not show_list:
            return

        match = process.extractOne(show_name, show_list.keys())

        return EntryMatch(
            show_name,
            show_list[match[0]],
            match[1]
        )


    async def check_item(self, item: dict) -> Optional[Tuple[int, int]]:
        """
        Checks an item to see if it is from a
        desired show entry, and will then begin
        downloading the item if so.

        Parameters
        ----------
        item: dict
            The item to check for matches.
        """
        # In case there are any errors with the user-defined parsing
        # functions, this try-except block will prevent the whole
        # poller task from crashing.
        try:
            if hasattr(self.current_parser, "ignore_logic"):
                if self.current_parser.ignore_logic(item) == False:
                    logger.debug(f"{self.current_parser.name} - Release Ignored")
                    return

            if hasattr(self.current_parser, "get_file_name"):
                torrent_name = self.current_parser.get_file_name(item)
            else:
                torrent_name = item["title"]

            show_name = self.current_parser.get_show_name(torrent_name)
            show_episode = self.current_parser.get_episode_number(torrent_name)
        except Exception as e:
            logger.error(f"Parsing Error - {e}")
            return

        if show_episode is None:
            return

        self.app.seen_titles.add(show_name)

        match = await self.check_item_for_match(show_name, show_episode)

        if match is None:
            return
        elif match.match_percent < 90:
            return

        entry_is_parsed = await self.is_parsed(match.matched_id, show_episode)
        if entry_is_parsed:
            return

        logger.info(f"{self.current_parser.name} - Release Found - {show_name}, {show_episode}")

        magnet_url = await self.get_torrent_link(item)
        await self.app.downloader.begin_handling(
            match.matched_id,
            show_episode,
            magnet_url
        )

        return (match.matched_id, show_episode)


    async def get_feed_from_parser(self, parser=None) -> dict:
        """
        Returns the RSS feed dict from the
        current parser.

        Returns
        -------
        dict
            The parsed RSS feed.
        """
        if self.current_parser is None:
            self.current_parser = parser

        return await self.loop.run_in_executor(None, feedparser.parse, self.current_parser.url)


    async def get_torrent_link(self, item: dict) -> str:
        """
        Returns a magnet URL for a specified item.
        This is found by using the parser's `get_link_location`
        method and is assisted by a torrent file to magnet
        decoder.

        Parameters
        ----------
        item: dict
            The item to find the magnet URL for.

        Returns
        -------
        str
            The found magnet URL.
        """
        client = self.app.dl_client

        if hasattr(self.current_parser, "get_link_location"):
            torrent_location = self.current_parser.get_link_location(item)
        else:
            torrent_location = item["link"]

        return await client.get_magnet(torrent_location)
