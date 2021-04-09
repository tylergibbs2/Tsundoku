from __future__ import annotations

import datetime
import logging
from typing import Optional

import aiohttp
from quart import current_app as app

from tsundoku.fluent import get_injector

API_URL = "https://kitsu.io/api/edge/anime"
logger = logging.getLogger("tsundoku")
resources = [
    "base",
    "errors",
    "index"
]

fluent = get_injector(resources)

status_html_map = {
    "current": f"<span class='img-overlay-span tag is-success noselect'>{fluent._('status-airing')}</span>",
    "finished": f"<span class='img-overlay-span tag is-danger noselect'>{fluent._('status-finished')}</span>",
    "tba": f"<span class='img-overlay-span tag is-warning noselect'>{fluent._('status-tba')}</span>",
    "unreleased": f"<span class='img-overlay-span tag is-info noselect'>{fluent._('status-unreleased')}</span>",
    "upcoming": f"<span class='img-overlay-span tag is-primary noselect'>{fluent._('status-upcoming')}</span>"
}


class KitsuManager:
    HEADERS = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json"
    }

    show_id: int

    kitsu_id: Optional[int]
    slug: Optional[str]
    status: Optional[str]
    poster: Optional[str]

    def __init__(self) -> None:
        self.SHOW_BASE = "https://kitsu.io/anime/{}"
        self.MEDIA_BASE = "https://media.kitsu.io/anime/poster_images/{}/{}.jpg"

    def to_dict(self) -> dict:
        """
        Serializes the KitsuManager object.

        Returns
        -------
        dict
            The serialized object.
        """
        return {
            "show_id": self.show_id,
            "kitsu_id": self.kitsu_id,
            "link": self.link,
            "slug": self.slug,
            "status": self.status,
            "html_status": status_html_map[self.status] if self.status else None,
            "poster": self.poster
        }

    @classmethod
    async def fetch(cls, show_id: int, show_name: str) -> KitsuManager:
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
        KitsuManager
            A KitsuManager for a show.
        """
        logger.info(f"Fetching Kitsu ID for Show {show_name}")

        async with aiohttp.ClientSession(headers=cls.HEADERS) as sess:
            payload = {
                "filter[text]": show_name,
                "fields[anime]": "id,status,slug"
            }
            async with sess.get(API_URL, params=payload) as resp:
                data = await resp.json()
                try:
                    result = data["data"][0]
                except (IndexError, KeyError):
                    result = {}

        attributes = result.get("attributes", {})

        instance = cls()
        instance.show_id = show_id
        instance.kitsu_id = int(result["id"]) if result else None
        instance.slug = attributes.get("slug")
        instance.status = attributes.get("status")

        instance.poster = await instance.get_poster_image()

        async with app.db_pool.acquire() as con:
            await con.execute("""
                DELETE FROM
                    kitsu_info
                WHERE
                    show_id=$1;
            """, show_id)
            await con.execute("""
                INSERT INTO
                    kitsu_info (
                        show_id,
                        kitsu_id,
                        slug,
                        show_status
                    )
                VALUES
                    ($1, $2, $3, $4);
            """, show_id, instance.kitsu_id, instance.slug, instance.status)

        return instance

    @classmethod
    async def fetch_by_kitsu(cls, show_id: int, kitsu_id: int) -> KitsuManager:
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
                "filter[id]": kitsu_id,
                "fields[anime]": "status,slug"
            }
            async with sess.get(API_URL, params=payload) as resp:
                data = await resp.json()
                try:
                    result = data["data"][0]
                except IndexError:
                    result = {}

        attributes = result.get("attributes", {})

        instance = cls()
        instance.show_id = show_id
        instance.kitsu_id = int(result["id"]) if result else None
        instance.slug = attributes.get("slug")
        instance.status = attributes.get("status")

        instance.poster = await instance.get_poster_image()

        async with app.db_pool.acquire() as con:
            await con.execute("""
                DELETE FROM
                    kitsu_info
                WHERE
                    show_id=$1;
            """, show_id)
            await con.execute("""
                INSERT INTO
                    kitsu_info (
                        show_id,
                        kitsu_id,
                        slug,
                        show_status
                    )
                VALUES
                    ($1, $2, $3, $4);
            """, show_id, instance.kitsu_id, instance.slug, instance.status)

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
                    show_status
                FROM
                    kitsu_info
                WHERE show_id=$1;
            """, show_id)
            if not row:
                show_name = await con.fetchval("""
                    SELECT
                        title
                    FROM
                        shows
                    WHERE id=$1;
                """, show_id)
                return await KitsuManager.fetch(show_id, show_name)

        instance = cls()
        instance.show_id = show_id
        instance.kitsu_id = row["kitsu_id"]
        instance.slug = row["slug"]
        instance.status = row["show_status"]

        instance.poster = await instance.get_poster_image()

        return instance

    @property
    def link(self) -> Optional[str]:
        """
        Returns the link to the show on Kitsu
        from the show's ID.

        Returns
        -------
        Optional[str]
            The show's link.
        """
        if self.kitsu_id:
            return self.SHOW_BASE.format(self.kitsu_id)
        else:
            return None

    async def clear_cache(self) -> None:
        """
        Clears the cached data for a show.
        """
        async with app.db_pool.acquire() as con:
            await con.execute("""
                DELETE FROM
                    kitsu_info
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

    async def should_update_status(self) -> bool:
        """
        Checks whether a Show's status should be
        updated.

        Status should be updated only if:
        - Time elapsed since last check > 2 days
        - Cached status is not "finished"
        - Show has a cached kitsu_id

        Returns
        -------
        bool
            Whether or not the show's status
            should be updated.
        """
        if self.kitsu_id is None:
            return False

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

        if row["last_updated"] is None:
            return True

        delta = now - row["last_updated"]

        if row["show_status"] == "finished" or delta.total_seconds() < (2 * 86400):
            return False

        return True

    async def set_status(self, status: str) -> None:
        """
        Updates the status of a Show.

        Parameters
        ----------
        status: str
            The new status.
        """
        if self.kitsu_id is None:
            return

        self.status = status
        now = datetime.datetime.utcnow()
        async with app.db_pool.acquire() as con:
            await con.execute("""
                UPDATE
                    kitsu_info
                SET
                    show_status=$1,
                    last_updated=$2
                WHERE kitsu_id=$3;
            """, status, now, self.kitsu_id)
