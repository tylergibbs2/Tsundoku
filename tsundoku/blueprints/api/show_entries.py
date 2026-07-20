from __future__ import annotations

import logging

from fastapi import APIRouter, Request, status

from tsundoku.auth import StateDep
from tsundoku.manager import Entry

from .response import APIError, Success
from .schemas import EntryCreate, ShowEntryRecord

logger = logging.getLogger("tsundoku")

router = APIRouter()


async def _add_single_entry(state: StateDep, show_id: int, entry: EntryCreate) -> Entry:
    if entry.magnet:
        magnet = await state.dl_client.get_magnet(entry.magnet)
        entry_id = await state.downloader.begin_handling(show_id, entry.episode, magnet, "v0", manual=True)
    else:
        async with state.acquire_db() as con, con.cursor() as cur:
            await cur.execute(
                """
                    INSERT INTO
                        show_entry (
                            show_id,
                            episode,
                            current_state,
                            torrent_hash,
                            created_manually
                        )
                    VALUES
                        (?, ?, ?, ?, ?);
                """,
                show_id,
                entry.episode,
                "completed",
                "",
                True,
            )
            entry_id = cur.lastrowid

    async with state.acquire_db() as con:
        new_entry = await con.fetchone(
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

    new_entry_obj = Entry.from_record(state, new_entry)
    logger.info(f"Entry Manually Added - <e{new_entry_obj.id}>")
    await new_entry_obj._handle_webhooks()
    return new_entry_obj


@router.get("/shows/{show_id}/entries")
async def get_show_entries(state: StateDep, show_id: int) -> Success[list[ShowEntryRecord]]:
    async with state.acquire_db() as con:
        entries = await con.fetchall(
            """
            SELECT
                id,
                episode,
                current_state,
                torrent_hash
            FROM
                show_entry
            WHERE show_id=?;
        """,
            show_id,
        )

    return Success(result=[ShowEntryRecord.model_validate(dict(record)) for record in entries])


@router.get("/shows/{show_id}/entries/{entry_id}")
async def get_show_entry(state: StateDep, show_id: int, entry_id: int) -> Success[ShowEntryRecord]:
    async with state.acquire_db() as con:
        entry = await con.fetchone(
            """
                SELECT
                    id,
                    episode,
                    current_state,
                    torrent_hash
                FROM
                    show_entry
                WHERE id=?;
            """,
            entry_id,
        )

    if entry is None:
        raise APIError(status.HTTP_404_NOT_FOUND, "Entry with specified ID does not exist.")

    return Success(result=ShowEntryRecord.model_validate(dict(entry)))


@router.post("/shows/{show_id}/entries", status_code=status.HTTP_201_CREATED)
async def create_show_entries(
    state: StateDep,
    show_id: int,
    request: Request,
) -> Success[Entry] | Success[list[Entry]]:
    body = await request.json()

    try:
        if isinstance(body, dict):
            entry = await _add_single_entry(state, show_id, EntryCreate.model_validate(body))
            return Success(status=status.HTTP_201_CREATED, result=entry)
        if isinstance(body, list):
            parsed = [EntryCreate.model_validate(item) for item in body]
            entries = [await _add_single_entry(state, show_id, item) for item in parsed]
            return Success(status=status.HTTP_201_CREATED, result=entries)
    except APIError:
        raise
    except Exception as e:
        raise APIError(status.HTTP_400_BAD_REQUEST, str(e)) from e

    raise APIError(status.HTTP_400_BAD_REQUEST, "Invalid request body.")


@router.delete("/shows/{show_id}/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_show_entry(state: StateDep, show_id: int, entry_id: int) -> None:
    async with state.acquire_db() as con:
        episode = await con.fetchval(
            """
            SELECT
                episode
            FROM
                show_entry
            WHERE id=?;
        """,
            entry_id,
        )

        await con.execute(
            """
            DELETE FROM
                show_entry
            WHERE id=?;
        """,
            entry_id,
        )

    logger.info(f"Entry Deleted - <s{show_id}>, episode {episode}")
