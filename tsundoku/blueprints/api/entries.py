import logging
from typing import Optional

from quart import current_app as app
from quart import request, views

from tsundoku.manager import Entry

from .response import APIResponse

logger = logging.getLogger("tsundoku")


class EntriesAPI(views.MethodView):
    async def get(self, show_id: int, entry_id: Optional[int]) -> APIResponse:
        if entry_id is None:
            async with app.acquire_db() as con:
                await con.execute("""
                    SELECT
                        id,
                        episode,
                        current_state,
                        torrent_hash
                    FROM
                        show_entry
                    WHERE show_id=?;
                """, show_id)
                entries = await con.fetchall()

            return APIResponse(
                result=[dict(record) for record in entries]
            )
        else:
            async with app.acquire_db() as con:
                await con.execute("""
                    SELECT
                        id,
                        episode,
                        current_state,
                        torrent_hash
                    FROM
                        show_entry
                    WHERE id=?;
                """, entry_id)
                entry = await con.fetchone()

            if entry is None:
                return APIResponse(
                    status=404,
                    error="Entry with specified ID does not exist."
                )

            return APIResponse(
                result=dict(entry)
            )

    async def post(self, show_id: int, entry_id: int = None) -> APIResponse:
        arguments = await request.get_json()
        required_arguments = {"episode", "magnet"}

        if all(arg not in arguments.keys() for arg in required_arguments):
            return APIResponse(
                status=400,
                error="Too many arguments or missing required argument."
            )

        try:
            episode = int(arguments["episode"])
        except ValueError:
            return APIResponse(
                status=400,
                error="Episode argument must be an integer."
            )

        if arguments["magnet"]:
            magnet = await app.dl_client.get_magnet(arguments["magnet"])
            entry_id = await app.downloader.begin_handling(show_id, episode, magnet)
        else:
            async with app.acquire_db() as con:
                await con.execute("""
                    INSERT INTO
                        show_entry (
                            show_id,
                            episode,
                            current_state,
                            torrent_hash
                        )
                    VALUES
                        (?, ?, ?, ?);
                """, show_id, episode, "completed", "")
                entry_id = con.lastrowid

        async with app.acquire_db() as con:
            await con.execute("""
                SELECT
                    id,
                    show_id,
                    episode,
                    current_state,
                    torrent_hash,
                    file_path,
                    last_update
                FROM
                    show_entry
                WHERE id=?;
            """, entry_id)
            new_entry = await con.fetchone()

        entry = Entry(app, new_entry)

        logger.info(f"Entry Manually Added - <e{entry.id}>")

        await entry._handle_webhooks()

        return APIResponse(
            result=entry.to_dict()
        )

    async def delete(self, show_id: int, entry_id: int) -> APIResponse:
        async with app.acquire_db() as con:
            await con.execute("""
                DELETE FROM
                    show_entry
                WHERE id=?;
            """, entry_id)

        logger.info(f"Entry Deleted - <e{entry_id}>")

        return APIResponse(
            result=True
        )
