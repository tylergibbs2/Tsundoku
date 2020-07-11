import aiohttp
import logging
from typing import Optional

from quart import current_app as app


KITSU_API = "https://kitsu.io/api/edge/anime"
KITSU_SHOW_BASE = "https://kitsu.io/anime/{}"
KITSU_MEDIA_BASE = "https://media.kitsu.io/anime/poster_images/{}/{}.jpg"
HEADERS = {
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/vnd.api+json"
}


logger = logging.getLogger("tsundoku")


async def get_id(show_name: str) -> Optional[int]:
    """
    Attempts to retrieve an image of the
    passed show name.

    Parameters
    ----------
    show_name: str
        The name of the show.

    Returns
    -------
    Optional[int]
        The ID of the show on Kitsu.
    """
    logger.info(f"Retrieving Kitsu ID for Show {show_name}")

    async with aiohttp.ClientSession(headers=HEADERS) as sess:
        payload = {
            "filter[text]": show_name
        }
        async with sess.get(KITSU_API, params=payload) as resp:
            data = await resp.json()
            try:
                result = data["data"][0]
            except IndexError:
                return

            return int(result["id"])

def get_link(show_id: int) -> str:
    """
    Returns the link to the show on Kitsu
    from the show's ID.

    Parameters
    ----------
    show_id: int
        The ID of the show.

    Returns
    -------
    str
        The show's link.
    """
    if show_id is None:
        return

    return KITSU_SHOW_BASE.format(show_id)

async def get_poster_image(show_id: int) -> str:
    """
    Returns the link to the show's poster
    with the specified size.

    Parameters
    ----------
    show_id: int
        The ID of the show.

    Returns
    -------
    str
        The desired poster.
    """
    if show_id is None:
        return

    async with app.db_pool.acquire() as con:
        url = await con.fetchval("""
            SELECT cached_poster_url FROM shows WHERE kitsu_id=$1;
        """, show_id)
        if url:
            return url

    logger.info(f"Retrieving new poster URL for Kitsu ID {show_id} from Kitsu")

    to_cache = None
    async with aiohttp.ClientSession() as sess:
        for size in ["large", "medium", "small", "tiny", "original"]:
            url = KITSU_MEDIA_BASE.format(show_id, size)
            async with sess.head(url) as resp:
                if resp.status == 404:
                    continue

                logger.info(f"New poster found for Kitsu ID {show_id} at [{size}] quality")
                to_cache = url
                break

    if to_cache is None:
        return

    async with app.db_pool.acquire() as con:
        await con.execute("""
            UPDATE shows SET cached_poster_url=$1 WHERE kitsu_id=$2;
        """, to_cache, show_id)

    return to_cache
