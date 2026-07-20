from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Query, status

from tsundoku.auth import StateDep
from tsundoku.constants import VALID_RESOLUTIONS
from tsundoku.manager import SeenRelease, Show, ShowCollection

from .response import APIError, Success
from .schemas import Pagination, ShowCreate, ShowsPage, ShowUpdate

logger = logging.getLogger("tsundoku")

router = APIRouter()


@router.get("/shows")
async def get_shows(
    state: StateDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 17,
    filters: str | None = None,
    text_filter: str | None = None,
    sort_key: str = "title",
    sort_direction: str = "+",
) -> Success[ShowsPage]:
    offset = (page - 1) * limit

    statuses = [f.strip() for f in filters.split(",") if f.strip()] if filters else []
    shows, total_count = await ShowCollection.filtered_paginated(
        state,
        statuses,
        limit,
        offset,
        text_filter or None,
        sort_key,
        sort_direction,
    )
    await shows.gather_statuses()

    page_payload = ShowsPage(
        shows=shows.shows,
        pagination=Pagination(
            page=page,
            limit=limit,
            total=total_count,
            pages=(total_count + limit - 1) // limit,
        ),
    )
    return Success(result=page_payload)


@router.get("/shows/{show_id}")
async def get_show(state: StateDep, show_id: int) -> Success[Show]:
    try:
        show = await Show.from_id(state, show_id)
    except ValueError as e:
        raise APIError(status.HTTP_404_NOT_FOUND, "Show with passed ID not found.") from e

    return Success(result=show)


@router.post("/shows", status_code=status.HTTP_201_CREATED)
async def create_show(state: StateDep, body: ShowCreate) -> Success[Show]:
    preferred_resolution = None if body.preferred_resolution == "0" else (body.preferred_resolution or None)

    if preferred_resolution is not None and preferred_resolution not in VALID_RESOLUTIONS:
        raise APIError(status.HTTP_400_BAD_REQUEST, "Preferred resolution is not a valid resolution.")

    show = await Show.insert(
        state,
        library_id=body.library_id,
        title=body.title,
        title_local=body.title_local or None,
        desired_format=body.desired_format or None,
        season=body.season,
        episode_offset=body.episode_offset,
        watch=body.watch,
        preferred_resolution=preferred_resolution,
        preferred_release_group=body.preferred_release_group or None,
    )

    async with state.acquire_db() as con:
        await con.execute(
            """
            INSERT OR IGNORE INTO
                webhook
                (show_id, base)
            SELECT (?), id FROM webhook_base;
        """,
            show.id_,
        )

    show = await Show.from_id(state, show.id_)
    for webhook in await show.load_webhooks():
        await webhook.import_default_triggers()

    if show.watch:
        logger.info(f"New Show Added, <s{show.id_}> - Preparing to Check for New Releases")

        # Find already seen releases. Must be done before triggering the poller.
        if show.preferred_resolution is not None and show.preferred_release_group is not None:
            seen_releases = await SeenRelease.filter(
                state,
                title=show.title,
                resolution=show.preferred_resolution,
                release_group=show.preferred_release_group,
            )
            for seen_release in seen_releases:
                magnet = await state.dl_client.get_magnet(seen_release.torrent_destination)
                await state.downloader.begin_handling(show.id_, seen_release.episode, magnet, seen_release.version)
        else:
            await state.poller.poll(force=True)

        # Refetch entries in case they were added during the poll.
        await show.load_entries()
    else:
        logger.info(f"New Show Added, <s{show.id_}> - Watch flag not set, not checking for new releases")

    return Success(status=status.HTTP_201_CREATED, result=show)


@router.put("/shows/{show_id}")
async def update_show(state: StateDep, show_id: int, body: ShowUpdate) -> Success[Show]:
    try:
        show = await Show.from_id(state, show_id)
    except Exception as e:
        raise APIError(status.HTTP_404_NOT_FOUND, "Show with passed ID not found.") from e

    # `lazy_metadata` defaults to False, so metadata is always populated here.
    assert show.metadata is not None

    preferred_resolution = None if body.preferred_resolution == "0" else (body.preferred_resolution or None)

    if preferred_resolution is not None and preferred_resolution not in VALID_RESOLUTIONS:
        raise APIError(status.HTTP_400_BAD_REQUEST, "Preferred resolution is not a valid resolution.")

    show.library_id = body.library_id
    show.preferred_resolution = preferred_resolution
    show.preferred_release_group = body.preferred_release_group or None
    show.desired_format = body.desired_format or None

    if body.season is not None:
        show.season = body.season

    if body.episode_offset is not None:
        show.episode_offset = body.episode_offset

    do_poll = False

    old_title = show.title
    old_kitsu = show.metadata.kitsu_id

    if old_title != body.title:
        do_poll = True
        await show.metadata.fetch(state, show_id, body.title)

    if body.kitsu_id is not None and old_kitsu != body.kitsu_id:
        await show.metadata.fetch_by_kitsu(state, show_id, body.kitsu_id)

    if body.title:
        show.title = body.title

    if body.watch is not None:
        show.watch = body.watch

    show.title_local = body.title_local or None

    await show.update()

    if do_poll:
        logger.info(f"Existing Show Updated, <s{show_id}> - Preparing to Check for New Releases")
        await state.poller.poll(force=True)

    show = await Show.from_id(state, show_id)

    return Success(result=show)


@router.delete("/shows/{show_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_show(state: StateDep, show_id: int) -> None:
    async with state.acquire_db() as con:
        title = await con.fetchval(
            """
            SELECT
                title
            FROM
                shows
            WHERE
                id=?
        """,
            show_id,
        )

        await con.execute(
            """
            DELETE FROM
                shows
            WHERE id=?;
        """,
            show_id,
        )

    logger.info(f"Show Deleted - {title}")
