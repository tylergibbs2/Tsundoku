from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Query, status

from tsundoku.auth import StateDep
from tsundoku.manager import Entry
from tsundoku.nyaa import NyaaSearcher, SearchResult

from .response import APIError, Success
from .schemas import NyaaResult, NyaaShowRequest

logger = logging.getLogger("tsundoku")

router = APIRouter()


@router.get("/nyaa")
async def search_nyaa(
    state: StateDep,
    query: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 15,
    page: Annotated[int, Query(ge=1)] = 1,
) -> Success[list[NyaaResult]]:
    if not query:
        return Success(result=[])

    try:
        results = await NyaaSearcher.search(state, query, limit=limit, page=page)
    except Exception as e:
        logger.error(f"Nyaa API - Search Error: {e}", exc_info=True)
        raise APIError(status.HTTP_400_BAD_REQUEST, "Error searching for the specified query.") from e

    return Success(result=[NyaaResult.from_search_result(sr) for sr in results])


@router.post("/nyaa")
async def add_nyaa_result(state: StateDep, body: NyaaShowRequest) -> Success[list[Entry]]:
    async with state.acquire_db() as con:
        show_id = await con.fetchval(
            """
            SELECT
                id
            FROM
                shows
            WHERE id=?;
        """,
            body.show_id,
        )

    if not show_id:
        raise APIError(status.HTTP_404_NOT_FOUND, "Show ID does not exist in the database.")

    search_result = SearchResult.from_necessary(state, show_id, body.torrent_link)

    logger.info(f"Processing new search result for Show <s{show_id}>")

    entries = await search_result.process(overwrite=body.overwrite)

    return Success(result=entries)
