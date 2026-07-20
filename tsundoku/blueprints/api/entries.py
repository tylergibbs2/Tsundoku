from __future__ import annotations

import logging

from fastapi import APIRouter, status

from tsundoku.auth import StateDep
from tsundoku.manager import Entry

from .response import APIError, Success

logger = logging.getLogger("tsundoku")

router = APIRouter()


@router.get("/entries/{entry_id}")
async def get_entry(state: StateDep, entry_id: int) -> Success[Entry]:
    async with state.acquire_db() as con:
        entry = await con.fetchone(
            """
            SELECT
                id,
                show_id,
                episode,
                version,
                current_state,
                torrent_hash,
                file_path,
                created_manually,
                last_update
            FROM
                show_entry
            WHERE id=?;
        """,
            entry_id,
        )

    if entry is None:
        raise APIError(status.HTTP_404_NOT_FOUND, "Entry with specified ID does not exist.")

    return Success(result=Entry.from_record(state, entry))
