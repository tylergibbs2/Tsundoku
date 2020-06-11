import aiohttp
import typing


KITSU_API = "https://kitsu.io/api/edge/anime"
KITSU_SHOW_BASE = "https://kitsu.io/anime/{}"
KITSU_MEDIA_BASE = "https://media.kitsu.io/anime/poster_images/{}/{}.jpg"
HEADERS = {
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/vnd.api+json"
}


async def get_id(show_name: str) -> typing.Optional[int]:
    """
    Attempts to retrieve an image of the
    passed show name.

    Parameters
    ----------
    show_name: str
        The name of the show.

    Returns
    -------
    typing.Optional[int]
        The ID of the show on Kitsu.
    """
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

    async with aiohttp.ClientSession() as sess:
        for size in ["large", "medium", "small", "tiny"]:
            url = KITSU_MEDIA_BASE.format(show_id, size)
            async with sess.head(url) as resp:
                if resp.status == 404:
                    continue

                return url
