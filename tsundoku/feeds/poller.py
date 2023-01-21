from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from functools import partial, cmp_to_key
import hashlib
import logging
import os
from sqlite3 import Row
from typing import Any, Dict, List, NamedTuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

import feedparser

from tsundoku.config import FeedsConfig
from tsundoku.feeds.fuzzy import extract_one
from tsundoku.manager import SeenRelease
from tsundoku.sources import get_all_sources, Source
from tsundoku.utils import (
    compare_version_strings,
    normalize_resolution,
    parse_anime_title,
)

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


class FoundEntry(NamedTuple):
    show_id: int
    episode: int


@dataclass
class SourceCache:
    """
    Represents a cache for a single RSS feed source.

    Attributes
    ----------
    last_etag: str
        The last ETag value for the feed.
    last_modified: str
        The last modified value for the feed.
    most_recent_hash: str
        The hash of the most recent item in the feed.
    """

    last_etag: Optional[str] = None
    last_modified: Optional[str] = None
    most_recent_hash: Optional[str] = None


class Poller:
    """
    The polling manager handles all RSS feed related
    activities.

    Once started, the manager will iterate through every
    enabled RSS feed source and parse their respective
    feeds using custom logic defined in each source.

    Items that are matched with the `shows` database will
    be then passed onto the download manager for downloading,
    renaming, and moving.
    """

    app: TsundokuApp
    source_cache: Dict[str, SourceCache]

    def __init__(self, app_context: Any) -> None:
        self.app = app_context.app
        self.loop = asyncio.get_running_loop()

        self.source_cache = defaultdict(SourceCache)

    async def update_config(self) -> None:
        """
        Updates the configuration for the task.
        """
        cfg = await FeedsConfig.retrieve(self.app)
        self.interval = cfg["polling_interval"]
        self.fuzzy_match_cutoff = cfg["fuzzy_cutoff"]

    async def start(self) -> None:
        """
        The program will poll every n seconds, as specified
        in the configuration file.
        """
        logger.debug("Poller task started.")

        if os.getenv("DISABLE_POLL_ON_START"):
            await self.update_config()
            logger.info(
                f"Polling disabled on start, waiting {self.interval} seconds before first poll..."
            )
            await asyncio.sleep(self.interval)

        while True:
            await self.update_config()

            try:
                await self.poll()
            except Exception:
                logger.error(
                    "An error occurred while polling RSS sources.", exc_info=True
                )

            try:
                await SeenRelease.delete_old(self.app, days=30)
            except Exception:
                logger.error(
                    "An error occurred while deleting old seen releases.", exc_info=True
                )

            logger.info(
                f"Sleeping {self.interval} seconds before polling RSS sources again..."
            )
            await asyncio.sleep(self.interval)

    def reset_rss_cache(self) -> None:
        """
        Resets all cache attributes on source
        objects for re-fetching the complete RSS
        feed.
        """
        self.source_cache.clear()

    async def poll(self, force: bool = False) -> List[FoundEntry]:
        """
        Iterates through every installed RSS source
        and will check for new items to download.

        Returns a list of releases found in the format
        (show_id, episode).

        Parameters
        ----------
        force: bool
            If True, will force a re-fetch of the RSS feed

        Returns
        -------
        List[FoundEntry]
            A list of tuples in the format (show_id, episode).
            These are newly found entries that have begun processing.
        """
        logger.info(f"Checking for New Releases... [force: {force}]")

        if force:
            self.reset_rss_cache()

        found = []

        async for source in get_all_sources():
            items = await self.get_items_from_source(source)
            if not items:
                continue

            logger.info(
                f"`{source.name}@{source.version}` - Checking for New Releases..."
            )
            source_items = await self.check_feed(source, items)
            found += source_items
            logger.info(
                f"`{source.name}@{source.version}` - Checked for New Releases, {len(source_items)} items found"
            )

        logger.info(f"Checked for New Releases, total of {len(found)} items found")

        # This still returns information, despite not being used in this particular
        # task, because the REST API hooks into the running Poller task and will call
        # this. See: tsundoku/blueprints/api/routes.py#check_for_releases
        return found

    async def check_feed(self, source: Source, items: List[dict]) -> List[FoundEntry]:
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
        List[FoundEntry]
            A list of tuples in the format (show_id, episode).
            These are newly found entries that have begun processing.
        """
        found_items = []

        for item in items:
            found = await self.check_item(source, item)
            if found:
                found_items.append(found)

        return found_items

    async def is_parsed(self, show_id: int, episode: int, version: str) -> bool:
        """
        Will check if a specified episode of a
        show has already been parsed.

        Parameters
        ----------
        show_id: int
            The ID of the show to check.
        episode: int
            The episode to check if it has been parsed.
        version: str
            The release version of the episode.

        Returns
        -------
        bool
            True if the episode has been parsed, False otherwise.
        """
        async with self.app.acquire_db() as con:
            entries = await con.fetchall(
                """
                SELECT
                    id,
                    version,
                    created_manually
                FROM
                    show_entry
                WHERE show_id=? AND episode=?;
            """,
                show_id,
                episode,
            )

        if not entries:
            return False

        def compare(first: Row, second: Row) -> int:
            return compare_version_strings(first["version"], second["version"])

        entries = sorted(entries, key=cmp_to_key(compare), reverse=True)

        return (
            entries[0]["created_manually"]
            or compare_version_strings(entries[0]["version"], version) >= 0
        )

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
            desired_shows = await con.fetchall(
                """
                SELECT
                    id,
                    title,
                    watch,
                    preferred_resolution,
                    preferred_release_group
                FROM
                    shows;
            """
            )
        show_list = {
            show["title"]: show["id"] for show in desired_shows if show["watch"]
        }

        if not show_list:
            return None

        # Extracts a tuple in the format (matched_str, percent_match)
        match = extract_one(show_name, list(show_list.keys()))

        if match:
            return EntryMatch(show_name, show_list[match[0]], match[1])

        return None

    async def check_item(self, source: Source, item: dict) -> Optional[FoundEntry]:
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
        Optional[FoundEntry]
            A tuple with (show_id, episode)
        """
        filename = source.get_filename(item)

        try:
            parsed = parse_anime_title(filename)
        except Exception:
            logger.exception(
                f"`{source.name}@{source.version}` - anitopy failed to parse '{filename}'",
                exc_info=True,
            )
            return None

        if parsed is None:
            logger.warning(
                f"`{source.name}@{source.version}` - anitopy failed to parse '{filename}'"
            )
            return None
        elif "anime_title" not in parsed:
            logger.warning(
                f"`{source.name}@{source.version}` - anitopy failed to retrieve 'anime_title' from '{filename}'"
            )
            return None
        elif "episode_number" not in parsed:
            logger.warning(
                f"`{source.name}@{source.version}` - anitopy failed to retrieve 'episode_number' from '{filename}'"
            )
            return None
        # elif "anime_type" in parsed.keys():
        #     print(parsed)
        #     logger.info(
        #         f"`{source.name}@{source.version}` - Ignoring non-episode '{filename}'"
        #     )
        #     return None
        elif "batch" in parsed.get("release_information", "").lower():
            logger.info(
                f"`{source.name}@{source.version}` - Ignoring batch release '{filename}'"
            )
            return None

        try:
            show_episode = int(parsed["episode_number"])
        except (ValueError, TypeError):
            logger.warning(
                f"`{source.name}@{source.version}` - Failed to convert episode '{parsed['episode_number']}' to integer from '{filename}'"
            )
            return None

        match = await self.check_item_for_match(parsed["anime_title"])

        if match is None or match.match_percent < self.fuzzy_match_cutoff:
            await SeenRelease.add(self.app, parsed, source.get_torrent(item))
            return None

        release_version = parsed.get("release_version", "v0")
        if not release_version.startswith("v"):
            release_version = f"v{release_version}"

        if await self.is_parsed(match.matched_id, show_episode, release_version):
            return None

        async with self.app.acquire_db() as con:
            preferences = await con.fetchone(
                """
                SELECT
                    preferred_resolution,
                    preferred_release_group
                FROM
                    shows
                WHERE
                    id=?;
            """,
                match.matched_id,
            )

        preferred_resolution = preferences["preferred_resolution"]
        preferred_release_group = preferences["preferred_release_group"]

        resolution = normalize_resolution(parsed.get("video_resolution", ""))
        release_group = parsed.get("release_group")
        if preferred_resolution is not None and resolution != preferred_resolution:
            logger.info(
                f"`{source.name}@{source.version}` - Ignoring release for '{filename}', resolution {resolution} does not match preferred resolution {preferred_resolution}"
            )
            return None
        elif (
            preferred_release_group is not None
            and release_group != preferred_release_group
        ):
            logger.info(
                f"`{source.name}@{source.version}` - Ignoring release for '{filename}', release group {release_group} does not match preferred release group {preferred_release_group}"
            )
            return None

        logger.info(
            f"`{source.name}@{source.version}` - Release Found for <s{match.matched_id}>, episode {show_episode}{release_version}"
        )

        magnet_url = await self.get_torrent_link(source, item)
        await self.app.downloader.begin_handling(
            match.matched_id, show_episode, magnet_url, release_version
        )

        return FoundEntry(match.matched_id, show_episode)

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

        return hashlib.sha256(to_hash.encode("utf-8")).hexdigest()

    async def get_items_from_source(self, source: Source) -> List[dict]:
        """
        Returns new items from the current
        source's RSS feed.

        Returns
        -------
        List[dict]
            New items in the RSS feed.
        """
        feed = await self.loop.run_in_executor(
            None,
            partial(
                feedparser.parse,
                source.url,
                etag=self.source_cache[source.name].last_etag,
                modified=self.source_cache[source.name].last_modified,
            ),
        )

        if hasattr(feed, "etag"):
            self.source_cache[source.name].last_etag = feed.etag
        else:
            self.source_cache[source.name].last_etag = None

        if hasattr(feed, "modified"):
            self.source_cache[source.name].last_modified = feed.modified
        else:
            self.source_cache[source.name].last_modified = None

        # 304 status means no new items according to the etag/modified attributes.
        if hasattr(feed, "status") and feed.status == 304:
            return []

        if (
            self.source_cache[source.name].last_etag is not None
            or self.source_cache[source.name].last_modified is not None
        ):
            return feed["items"]

        new_items = []

        # Since new items in the RSS feed are inserted at index 0,
        # the 0th index item is the most recent item in the feed.
        if feed["items"]:
            # If the first item in the feed is the same as it was
            # on the previous iteration, the feed has no new items.
            first_hash = self.hash_rss_item(feed["items"][0])
            if first_hash == self.source_cache[source.name].most_recent_hash:
                return []

            new_items.append(feed["items"][0])

            # Iterate through the rest of the items in the feed,
            # repeating the same process above.
            for item in feed["items"][1:]:
                item_hash = self.hash_rss_item(item)
                if item_hash == self.source_cache[source.name].most_recent_hash:
                    break

                new_items.append(item)

            self.source_cache[source.name].most_recent_hash = first_hash

        return new_items

    async def get_torrent_link(self, source: Source, item: dict) -> str:
        """
        Returns a magnet URL for a specified item.

        Parameters
        ----------
        item: dict
            The item to find the magnet URL for.

        Returns
        -------
        str
            The found magnet URL.
        """
        return await self.app.dl_client.get_magnet(source.get_torrent(item))
