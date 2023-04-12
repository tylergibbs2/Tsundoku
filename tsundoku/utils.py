from __future__ import annotations

import asyncio
from functools import partial, wraps
import logging
from pathlib import Path
import shutil
from typing import Any, List, TypedDict
from uuid import uuid4

import anitopy


def wrap(func: Any) -> Any:
    @wraps(func)
    async def run(
        *args: Any, loop: Any = None, executor: Any = None, **kwargs: Any
    ) -> Any:
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


move = wrap(shutil.move)
logger = logging.getLogger("tsundoku")


class ExprDict(dict):
    def __missing__(self, value: str) -> str:
        return value


class ParserResult(TypedDict, total=False):
    anime_title: str
    anime_year: str
    audio_term: str
    episode_number: List[str] | str
    episode_title: str
    file_checksum: str
    file_extension: str
    file_name: str
    release_group: str
    release_version: str
    release_information: str
    video_resolution: str
    video_term: str


def parse_anime_title(title: str) -> ParserResult:
    result: ParserResult = anitopy.parse(
        title, options={"allowed_delimiters": " _&+,|", "parse_episode_title": False}
    )  # type: ignore

    if "video_resolution" in result:
        result["video_resolution"] = normalize_resolution(result["video_resolution"])

    return result


def normalize_resolution(original: str) -> str:
    """
    Normalize a resolution string.

    Parameters
    ----------
    original: str
        The original resolution string.

    Returns
    -------
    str
        The normalized resolution string or the original
        if normalization was not possible.
    """
    original = original.lower().strip()
    if "x" in original:
        try:
            width, height, *_ = original.split("x")
            width, height = int(width.strip()), int(height.strip())
        except ValueError:
            return original.replace(" ", "")

        if height == 4320:
            return "8k"
        elif height == 3840:
            return "4k"
        elif height == 1080:
            return "1080p"
        elif height == 720:
            return "720p"
        elif height == 480:
            return "480p"
        elif height == 360:
            return "360p"

        return f"{width}x{height}"
    elif original.endswith("p"):
        if original == "4320p":
            return "8k"
        elif original == "2160p":
            return "4k"

    return original


def compare_version_strings(first: str, second: str) -> int:
    """
    Compare two version strings.

    Parameters
    ----------
    a: str
        The first version string.
    b: str
        The second version string.

    Returns
    -------
    int
        1 if a > b, -1 if a < b, 0 if a == b.
    """
    if first.startswith("v"):
        first = first[1:]
    if second.startswith("v"):
        second = second[1:]

    a = first.split(".")
    b = second.split(".")

    for i in range(max(len(a), len(b))):
        try:
            a_part = int(a[i])
        except IndexError:
            a_part = 0

        try:
            b_part = int(b[i])
        except IndexError:
            b_part = 0

        if a_part > b_part:
            return 1
        elif a_part < b_part:
            return -1

    return 0


def directory_is_writable(dir: Path) -> bool:
    logger.debug(f"Checking if directory '{dir}' is writable...")
    try:
        canary = dir / str(uuid4())
        canary.write_bytes(b"\0")
        canary.unlink(missing_ok=True)
    except Exception:
        return False

    return True
