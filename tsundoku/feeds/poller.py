import asyncio
import hashlib
import logging
from dataclasses import dataclass
from functools import partial
from typing import Any, List, Optional, Tuple

import feedparser

from tsundoku.config import get_config_value

from .fuzzy import extract_one

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

    def __init__(self, app_context: Any) -> None:
        self.app = app_context.app
        self.loop = asyncio.get_running_loop()

        self.current_parser: Any = None  # keeps track of the current parser

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
            try:
                await self.poll()
            except Exception:
                import traceback
                traceback.print_exc()

            await asyncio.sleep(self.interval)

    def reset_rss_cache(self) -> None:
        """
        Resets all cache attributes on parser
        objects for re-fetching the complete RSS
        feed.
        """
        for parser in self.app.rss_parsers:
            parser._last_etag = None
            parser._last_modified = None
            parser._most_recent_hash = None

    async def poll(self) -> List[Tuple[int, int]]:
        """
        Iterates through every installed RSS parser
        and will check for new items to download.

        The order of the parsers used is determined
        by how they are listed in the configuration.

        Returns a list of releases found in the format
        (show_id, episode).

        Returns
        -------
        List[Tuple[int, int]]
            A list of tuples in the format (show_id, episode).
            These are newly found entries that have begun processing.
        """
        logger.info("Checking for New Releases...")

        found = []

        for parser in self.app.rss_parsers:
            self.current_parser = parser
            items = await self.get_items_from_parser()
            if not items:
                continue

            logger.info(f"{parser.name} - Checking for New Releases...")
            found += await self.check_feed(items)
            logger.info(f"{parser.name} - Checked for New Releases")

        self.current_parser = None

        logger.info("Checked for New Releases")

        # This still returns information, despite not being used in this particular
        # task, because the REST API hooks into the running Poller task and will call
        # this. See: tsundoku/blueprints/api/routes.py#check_for_releases
        return found

    async def check_feed(self, items: List[dict]) -> List[Tuple[int, int]]:
        """
        Iterates through the list of items in an
        RSS feed and will individually check each
        item. Returns a list of tuples in the format
        (show_id, episode).

        Parameters
        ----------
        feed: dict
            The RSS feed items.

        Returns
        -------
        List[Tuple[int, int]]
            A list of tuples in the format (show_id, episode).
            These are newly found entries that have begun processing.
        """
        found_items = []

        for item in items:
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
        async with self.app.acquire_db() as con:
            await con.execute("""
                SELECT
                    id
                FROM
                    show_entry
                WHERE show_id=? AND episode=?;
            """, show_id, episode)
            show_entry = await con.fetchval()

        return bool(show_entry)

    async def check_item_for_match(self, show_name: str) -> Optional[EntryMatch]:
        """
        Takes a show name from RSS and an episode from RSS and
        checks if the object should be downloaded.

        An item should be downloaded only if it is in the
        `shows` table.

        Parameters
        ----------
        show_name: str
            The name of the show from RSS.

        Returns
        -------
        Optional[EntryMatch]
            The EntryMatch for the passed show name.
            Could be None if no shows are desired.
        """
        async with self.app.acquire_db() as con:
            await con.execute("""
                SELECT
                    id,
                    title
                FROM
                    shows;
            """)
            desired_shows = await con.fetchall()
        show_list = {show["title"]: show["id"] for show in desired_shows}

        if not show_list:
            return None

        # Extracts a tuple in the format (matched_str, percent_match)
        match = extract_one(show_name, list(show_list.keys()))

        if match:
            return EntryMatch(
                show_name,
                show_list[match[0]],
                match[1]
            )

        return None

    async def check_item(self, item: dict) -> Optional[Tuple[int, int]]:
        """
        Checks an item to see if it is from a
        desired show entry, and will then begin
        downloading the item if so.

        Parameters
        ----------
        item: dict
            The item to check for matches.

        Returns
        -------
        Optional[Tuple[int, int]]
            A tuple with (show_id, episode)
        """
        # In case there are any errors with the user-defined parsing
        # functions, this try-except block will prevent the whole
        # poller task from crashing.
        try:
            if self.current_parser.ignore_logic(item) is False:
                logger.debug(f"{self.current_parser.name} - Release Ignored")
                return None
        except AttributeError:
            pass  # The parser doesn't have an ignore_logic method.

        try:
            if hasattr(self.current_parser, "get_file_name"):
                torrent_name = self.current_parser.get_file_name(item)
            else:
                torrent_name = item["title"]

            show_name = self.current_parser.get_show_name(torrent_name)
            show_episode = self.current_parser.get_episode_number(torrent_name)
        except Exception as e:
            logger.error(
                f"Parsing Error - {self.current_parser.name}@{self.current_parser.version}: {e}")
            return None

        if show_episode is None:
            return None

        self.app.seen_titles.add(show_name)

        match = await self.check_item_for_match(show_name)

        if match is None or match.match_percent < 90:
            return None

        entry_is_parsed = await self.is_parsed(match.matched_id, show_episode)
        if entry_is_parsed:
            return None

        logger.info(
            f"{self.current_parser.name} - Release Found - {show_name}, {show_episode}")

        magnet_url = await self.get_torrent_link(item)
        await self.app.downloader.begin_handling(
            match.matched_id,
            show_episode,
            magnet_url
        )

        return (match.matched_id, show_episode)

    def hash_rss_item(self, item: dict) -> str:
        """
        Generates a unique hash for an RSS item based
        off of the item's title and/or description.

        https://www.rssboard.org/rss-profile#element-channel-item

        Parameters
        ----------
        item: dict
            The item to hash.

        Returns
        -------
        str
            SHA-256 hash of the item.
        """
        # RSS feed items are required to have at least one of these
        # attributes. See link in docstring for more details.
        to_hash = item.get("title", "") + item.get("description", "")

        return hashlib.sha256(
            to_hash.encode("utf-8")
        ).hexdigest()

    async def get_items_from_parser(self) -> List[dict]:
        """
        Returns new items from the current
        parser's RSS feed.

        Returns
        -------
        List[dict]
            New items in the RSS feed.
        """
        if not hasattr(self.current_parser, "_last_etag"):
            self.current_parser._last_etag = None

        if not hasattr(self.current_parser, "_last_modified"):
            self.current_parser._last_modified = None

        # The last_etag and last_modified attributes are going to
        # be private due to the fact that `self.current_parser` is
        # a user-defined class and there's an off-chance they could
        # use these names.

        feed = await self.loop.run_in_executor(None, partial(
            feedparser.parse,
            self.current_parser.url,
            etag=self.current_parser._last_etag,
            modified=self.current_parser._last_modified
        ))

        # None of the RSS URLs that I provide with this software out-of-the-box
        # provide etag or modified headers, but it's entirely possible a user-provided
        # URL will.
        try:
            self.current_parser._last_etag = feed.etag
        except AttributeError:
            self.current_parser._last_etag = None

        try:
            self.current_parser._last_modified = feed.modified
        except AttributeError:
            self.current_parser._last_modified = None

        # 304 status means no new items according to the etag/modified attributes.
        if hasattr(feed, "status") and feed.status == 304:
            return []

        if self.current_parser._last_etag is not None or self.current_parser._last_modified is not None:
            return feed["items"]

        # Worst-case scenario, etag header and modified header weren't
        # implemented on the server-side. Manually check unique item hashes
        # for all items in the feed.
        if not hasattr(self.current_parser, "_most_recent_hash"):
            self.current_parser._most_recent_hash = None

        new_items = []

        # Since new items in the RSS feed are inserted at index 0,
        # the 0th index item is the most recent item in the feed.
        if feed["items"]:
            # If the first item in the feed is the same as it was
            # on the previous iteration, the feed has no new items.
            first_hash = self.hash_rss_item(feed["items"][0])
            if first_hash == self.current_parser._most_recent_hash:
                return []

            new_items.append(feed["items"][0])

            # Iterate through the rest of the items in the feed,
            # repeating the same process above.
            for item in feed["items"][1:]:
                item_hash = self.hash_rss_item(item)
                if item_hash == self.current_parser._most_recent_hash:
                    break

                new_items.append(item)

            self.current_parser._most_recent_hash = first_hash

        return new_items

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
