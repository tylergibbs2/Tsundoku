import asyncio
from functools import partial, wraps
import logging
from pathlib import Path
import shutil
from typing import TYPE_CHECKING, Any, TypedDict, cast
from uuid import uuid4

from anitomy_ng import ElementKind, Options
from anitomy_ng import parse as anitomy_parse
from anitomy_ng import parse_together as anitomy_parse_together

if TYPE_CHECKING:
    from collections.abc import Iterable

    from anitomy_ng import Element


def wrap(func: Any) -> Any:
    @wraps(func)
    async def run(*args: Any, loop: Any = None, executor: Any = None, **kwargs: Any) -> Any:
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
    anime_type: str
    anime_year: str
    audio_term: str
    episode_number: list[str] | str
    episode_title: str
    file_checksum: str
    file_extension: str
    file_name: str
    release_group: str
    release_version: str
    release_information: str
    video_resolution: str
    video_term: str


# Maps anitomy-ng element kinds onto the ParserResult keys the rest of
# Tsundoku expects.
_KIND_TO_KEY: dict[ElementKind, str] = {
    ElementKind.TITLE: "anime_title",
    ElementKind.TYPE: "anime_type",
    ElementKind.YEAR: "anime_year",
    ElementKind.AUDIO_TERM: "audio_term",
    ElementKind.EPISODE: "episode_number",
    ElementKind.EPISODE_TITLE: "episode_title",
    ElementKind.FILE_CHECKSUM: "file_checksum",
    ElementKind.FILE_EXTENSION: "file_extension",
    ElementKind.RELEASE_GROUP: "release_group",
    ElementKind.RELEASE_VERSION: "release_version",
    ElementKind.RELEASE_INFORMATION: "release_information",
    ElementKind.VIDEO_RESOLUTION: "video_resolution",
    ElementKind.VIDEO_TERM: "video_term",
}

_PARSE_OPTIONS = Options(parse_episode_title=False)


def _elements_to_result(title: str, elements: "Iterable[Element]") -> ParserResult:
    grouped: dict[str, list[str]] = {}
    for element in elements:
        key = _KIND_TO_KEY.get(element.kind)
        if key is not None:
            grouped.setdefault(key, []).append(element.value)

    # anitomy-ng returns an ordered list of elements and may emit the same kind
    # more than once (e.g. the two endpoints of an episode range). A single
    # occurrence collapses to a bare string; a repeated key stays a list, which
    # the rest of the codebase branches on to detect batches/ranges.
    raw: dict[str, Any] = {"file_name": title}
    for key, values in grouped.items():
        raw[key] = values[0] if len(values) == 1 else values

    result = cast(ParserResult, raw)
    if "video_resolution" in result:
        result["video_resolution"] = normalize_resolution(result["video_resolution"])

    return result


def parse_anime_title(title: str) -> ParserResult:
    return _elements_to_result(title, anitomy_parse(title, _PARSE_OPTIONS))


def parse_anime_titles(titles: list[str]) -> list[ParserResult]:
    """
    Parse a set of *related* anime filenames together.

    Only use this for filenames that belong to the same release (e.g. the
    files inside a single torrent) — anitomy-ng shares context across the set
    to resolve ambiguities a single filename can't, such as a season-pack
    folder range versus the real per-file episode number. Do not use it for
    unrelated items (e.g. a mixed RSS feed), which would cross-contaminate.

    Results are returned in the same order as ``titles``.
    """
    return [_elements_to_result(title, elements) for title, elements in zip(titles, anitomy_parse_together(titles, _PARSE_OPTIONS), strict=True)]


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
        if height == 3840:
            return "4k"
        if height == 1080:
            return "1080p"
        if height == 720:
            return "720p"
        if height == 480:
            return "480p"
        if height == 360:
            return "360p"

        return f"{width}x{height}"
    if original.endswith("p"):
        if original == "4320p":
            return "8k"
        if original == "2160p":
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
    first = first.removeprefix("v")
    second = second.removeprefix("v")

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
        if a_part < b_part:
            return -1

    return 0


def directory_is_writable(directory: Path) -> bool:
    logger.debug(f"Checking if directory '{directory}' is writable...")
    try:
        canary = directory / str(uuid4())
        canary.write_bytes(b"\0")
        canary.unlink(missing_ok=True)
    except Exception:
        return False

    return True
