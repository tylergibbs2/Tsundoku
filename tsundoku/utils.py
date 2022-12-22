import asyncio
from functools import partial, wraps
import shutil
from typing import Any


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


class ExprDict(dict):
    def __missing__(self, value: str) -> str:
        return value


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
