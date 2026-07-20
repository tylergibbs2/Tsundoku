from __future__ import annotations

import logging

from fastapi import APIRouter, status

from tsundoku.auth import StateDep
from tsundoku.manager import SeenRelease
from tsundoku.nyaa import NyaaSearcher
from tsundoku.utils import parse_anime_title

from .response import APIError, Success
from .schemas import SeenReleaseAddRequest, SeenReleaseAddResult

logger = logging.getLogger("tsundoku")

router = APIRouter()


@router.get("/seen_releases/filter")
async def filter_seen_releases(
    state: StateDep,
    title: str | None = None,
    release_group: str | None = None,
    resolution: str | None = None,
    episode: int | None = None,
) -> Success[list[SeenRelease]]:
    releases = await SeenRelease.filter(
        state,
        title=title,
        release_group=release_group,
        resolution=resolution,
        episode=episode,
    )
    return Success(result=releases)


@router.get("/seen_releases/distinct")
async def distinct_seen_releases(
    state: StateDep,
    field: str,
    title: str | None = None,
    release_group: str | None = None,
    resolution: str | None = None,
) -> Success[list[str]]:
    try:
        values = await SeenRelease.distinct(
            state,
            field,
            title=title,
            release_group=release_group,
            resolution=resolution,
        )
    except ValueError as e:
        raise APIError(status.HTTP_400_BAD_REQUEST, str(e)) from e

    return Success(result=values)


@router.post("/seen_releases/add")
async def add_seen_releases(state: StateDep, body: SeenReleaseAddRequest) -> Success[SeenReleaseAddResult]:
    """
    Searches Nyaa for a title/release group and persists any results as
    seen releases, keyed to the caller's chosen title/group so that adding
    the show later pulls them in. Returns how many *additional* releases now
    match the (title, release group, resolution) criteria and the resulting
    episode list.
    """

    async def matching_episodes() -> set[int]:
        releases = await SeenRelease.filter(
            state,
            title=body.title,
            release_group=body.release_group,
            resolution=body.resolution,
        )
        return {release.episode for release in releases}

    before = await matching_episodes()

    try:
        results = await NyaaSearcher.search(state, f"[{body.release_group}] {body.title}", limit=75, page=1)
    except Exception as e:
        logger.error(f"Seen Releases API - Nyaa search error: {e}", exc_info=True)
        raise APIError(status.HTTP_400_BAD_REQUEST, "Error searching Nyaa for more releases.") from e

    for result in results:
        parsed = parse_anime_title(result.title)
        # Persist under the caller's chosen title/group so the add-time
        # filter (title + release_group + resolution) pulls these in.
        # Resolution is left as parsed so a mismatched result isn't misfiled.
        parsed["anime_title"] = body.title
        parsed["release_group"] = body.release_group

        await SeenRelease.add(state, parsed, result.torrent_link)

    after = await matching_episodes()

    return Success(
        result=SeenReleaseAddResult(
            additional=len(after - before),
            episodes=sorted(after),
        )
    )
