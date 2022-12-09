import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

    app: TsundokuApp
else:
    from quart import current_app as app

from quart import request, views

from tsundoku.manager import Entry

from .response import APIResponse

logger = logging.getLogger("tsundoku")


class ShowEntriesAPI(views.MethodView):
    async def get(self, show_id: int, entry_id: Optional[int]) -> APIResponse:
        if entry_id is None:
            async with app.acquire_db() as con:
                await con.execute(
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
                entries = await con.fetchall()

            return APIResponse(result=[dict(record) for record in entries])
        else:
            async with app.acquire_db() as con:
                await con.execute(
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
                entry = await con.fetchone()

            if entry is None:
                return APIResponse(
                    status=404, error="Entry with specified ID does not exist."
                )

            return APIResponse(result=dict(entry))

    async def add_single_entry(self, show_id: int, entry: dict) -> Entry:
        required_arguments = {"episode", "magnet"}
        if all(arg not in entry.keys() for arg in required_arguments):
            raise Exception(
                f"Too many arguments or missing required arguments ({', '.join(required_arguments)})."
            )

        try:
            episode = int(entry["episode"])
        except ValueError:
            raise Exception("Episode must be an integer.")

        if entry["magnet"]:
            magnet = await app.dl_client.get_magnet(entry["magnet"])
            entry_id = await app.downloader.begin_handling(
                show_id, episode, magnet, "v0", manual=True
            )
        else:
            async with app.acquire_db() as con:
                await con.execute(
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
                    episode,
                    "completed",
                    "",
                    True,
                )
                entry_id = con.lastrowid

        async with app.acquire_db() as con:
            await con.execute(
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
            new_entry = await con.fetchone()

        new_entry_obj = Entry(app, new_entry)
        logger.info(f"Entry Manually Added - <e{new_entry_obj.id}>")
        await new_entry_obj._handle_webhooks()
        return new_entry_obj

    async def post(self, show_id: int, entry_id: Optional[int] = None) -> APIResponse:
        body = await request.get_json()

        try:
            if isinstance(body, dict):
                entry = await self.add_single_entry(show_id, body)
                return APIResponse(result=entry.to_dict())
            elif isinstance(body, list):
                entries = [
                    await self.add_single_entry(show_id, entry) for entry in body
                ]
                return APIResponse(result=[entry.to_dict() for entry in entries])
        except Exception as e:
            return APIResponse(status=400, error=str(e))

        return APIResponse(status=400, error="Invalid request body.")

    async def delete(self, show_id: int, entry_id: int) -> APIResponse:
        async with app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    episode
                FROM
                    show_entry
                WHERE id=?;
            """,
                entry_id,
            )

            episode = await con.fetchval()

            await con.execute(
                """
                DELETE FROM
                    show_entry
                WHERE id=?;
            """,
                entry_id,
            )

        logger.info(f"Entry Deleted - <s{show_id}>, episode {episode}")

        return APIResponse(result=True)
