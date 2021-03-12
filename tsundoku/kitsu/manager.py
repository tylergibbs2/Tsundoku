from __future__ import annotations

import datetime
import logging
from typing import Dict, List, Optional

import aiohttp
from quart import current_app as app

API_URL = "https://kitsu.io/api/edge/anime"
logger = logging.getLogger("tsundoku")


async def gather_statuses(managers: List[KitsuManager]) -> None:
    to_retrieve: List[int] = []

    for manager in managers:
        to_retrieve.append(manager.kitsu_id)

    async with aiohttp.ClientSession() as sess:
        payload = {
            "filter[id]": ",".join(map(str, to_retrieve)),
            "fields[anime]": "status"
        }
        async with sess.get(API_URL, params=payload) as resp:
            data = await resp.json()
            for i in range(len(to_retrieve)):
                try:
                    show_response: Dict = data["data"][i]
                    status = show_response.get("attributes", {}).get("status", None)
                    managers[i].status = status
                except IndexError:
                    pass


class KitsuManager:
    HEADERS = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json"
    }

    show_id: int
    kitsu_id: int
    slug: str

    status: Optional[str]

    def __init__(self) -> None:
        self.SHOW_BASE = "https://kitsu.io/anime/{}"
        self.MEDIA_BASE = "https://media.kitsu.io/anime/poster_images/{}/{}.jpg"

    @classmethod
    async def fetch(cls, show_id: int, show_name: str) -> Optional[KitsuManager]:
        """
        Attempts to retrieve Kitsu information
        for a specified show name from the Kitsu API.

        Parameters
        ----------
        show_id: int
            The show's ID.
        show_name: str
            The name of the show.

        Returns
        -------
        Optional[KitsuManager]
            A KitsuManager for a show.
        """
        logger.info(f"Fetching Kitsu ID for Show {show_name}")

        async with aiohttp.ClientSession(headers=cls.HEADERS) as sess:
            payload = {
                "filter[text]": show_name
            }
            async with sess.get(API_URL, params=payload) as resp:
                data = await resp.json()
                try:
                    result = data["data"][0]
                except (IndexError, KeyError):
                    return None

        if not result or not result.get("id"):
            return None

        instance = cls()
        instance.kitsu_id = int(result["id"])
        instance.slug = result.get("slug")

        instance.status = None

        async with app.db_pool.acquire() as con:
            await con.execute("""
                DELETE FROM
                    kitsu_info
                WHERE
                    show_id=$1;
            """, show_id)
            await con.execute("""
                INSERT INTO
                    kitsu_info
                    (show_id, kitsu_id, slug)
                VALUES
                    ($1, $2, $3);
            """, show_id, instance.kitsu_id, instance.slug)

        return instance

    @classmethod
    async def fetch_by_kitsu(cls, show_id: int, kitsu_id: int) -> Optional[KitsuManager]:
        """
        Attempts to retrieve Kitsu information
        for a specified show ID from the Kitsu API.

        Parameters
        ----------
        show_id: int
            The show's ID.
        kitsu_id: int
            The name of the show.

        Returns
        -------
        Optional[KitsuManager]
            A KitsuManager for a show.
        """
        logger.info(f"Fetching Kitsu ID for Show #{show_id}")

        async with aiohttp.ClientSession(headers=cls.HEADERS) as sess:
            payload = {
                "filter[id]": kitsu_id
            }
            async with sess.get(API_URL, params=payload) as resp:
                data = await resp.json()
                try:
                    result = data["data"][0]
                except IndexError:
                    return None

        if not result or not result.get("id"):
            return None

        instance = cls()
        instance.kitsu_id = int(result["id"])
        instance.slug = result.get("slug")

        instance.status = None

        async with app.db_pool.acquire() as con:
            await con.execute("""
                DELETE FROM
                    kitsu_info
                WHERE
                    show_id=$1;
            """, show_id)
            await con.execute("""
                INSERT INTO
                    kitsu_info
                    (show_id, kitsu_id, slug)
                VALUES
                    ($1, $2, $3);
            """, show_id, instance.kitsu_id, instance.slug)

        return instance

    @classmethod
    async def from_show_id(cls, show_id: int) -> KitsuManager:
        """
        Retrieves Kitsu information from the database based
        on a show's ID.

        Parameters
        ----------
        show_id: int
            The show's ID in the database.

        Returns
        -------
        KitsuManager
            A KitsuManager for the show.
        """
        logger.info(f"Retrieving existing Kitsu info for Show ID #{show_id}")

        async with app.db_pool.acquire() as con:
            row = await con.fetchrow("""
                SELECT
                    kitsu_id,
                    slug,
                    last_updated
                FROM
                    kitsu_info
                WHERE show_id=$1;
            """, show_id)
            if not row:
                raise Exception(f"KitsuManager for Show ID # {show_id} is missing.")

        instance = cls()
        instance.kitsu_id = row["kitsu_id"]
        instance.slug = row["slug"]

        instance.status = None

        return instance

    @property
    def link(self) -> str:
        """
        Returns the link to the show on Kitsu
        from the show's ID.

        Returns
        -------
        str
            The show's link.
        """
        return self.SHOW_BASE.format(self.kitsu_id)

    async def clear_cache(self) -> None:
        """
        Clears the cached data for a show.
        """
        async with app.db_pool.acquire() as con:
            await con.execute("""
                UPDATE
                    kitsu_info
                SET
                    show_status = NULL,
                    cached_poster_url = NULL
                WHERE
                    show_id=$1;
            """, self.show_id)

    async def get_poster_image(self) -> Optional[str]:
        """
        Returns the link to the show's poster.

        Returns
        -------
        Optional[str]
            The desired poster.
        """
        if self.kitsu_id is None:
            return None

        async with app.db_pool.acquire() as con:
            url = await con.fetchval("""
                SELECT
                    cached_poster_url
                FROM
                    kitsu_info
                WHERE kitsu_id=$1;
            """, self.kitsu_id)
            if url:
                return url

        logger.info(f"Retrieving new poster URL for Kitsu ID {self.kitsu_id} from Kitsu")

        to_cache = None
        async with aiohttp.ClientSession() as sess:
            for size in ["large", "medium", "small", "tiny", "original"]:
                url = self.MEDIA_BASE.format(self.kitsu_id, size)
                async with sess.head(url) as resp:
                    if resp.status == 404:
                        continue

                    logger.info(f"New poster found for Kitsu ID {self.kitsu_id} at [{size}] quality")
                    to_cache = url
                    break

        if to_cache is None:
            return None

        async with app.db_pool.acquire() as con:
            await con.execute("""
                UPDATE
                    kitsu_info
                SET
                    cached_poster_url=$1
                WHERE kitsu_id=$2;
            """, to_cache, self.kitsu_id)

        return to_cache

    async def get_status(self) -> Optional[str]:
        """
        Returns the status of the show.

        Returns
        -------
        Optional[str]
            The show's airing status.
        """
        if self.kitsu_id is None:
            return None

        async with app.db_pool.acquire() as con:
            row = await con.fetchrow("""
                SELECT
                    show_status,
                    last_updated
                FROM
                    kitsu_info
                WHERE kitsu_id=$1;
            """, self.kitsu_id)

        now = datetime.datetime.utcnow()
        delta = now - row["last_updated"]

        if row["show_status"] == "finished" or (delta.total_seconds() < 86400 and row["show_status"]):
            return row["show_status"]

        logger.info(f"Retrieving new show status for Kitsu ID {self.kitsu_id} from Kitsu")

        to_cache = None
        async with aiohttp.ClientSession() as sess:
            payload = {
                "filter[id]": self.kitsu_id,
                "fields[anime]": "status"
            }
            async with sess.get(API_URL, params=payload) as resp:
                data = await resp.json()
                try:
                    to_cache = data["data"][0]
                except IndexError:
                    return None

        if to_cache is None:
            return None

        status = to_cache.get("attributes", {}).get("status")

        async with app.db_pool.acquire() as con:
            await con.execute("""
                UPDATE
                    kitsu_info
                SET
                    show_status=$1,
                    last_updated=$2
                WHERE kitsu_id=$3;
            """, status, now, self.kitsu_id)

        return status
