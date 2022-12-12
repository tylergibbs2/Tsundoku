import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

    app: TsundokuApp
else:
    from quart import current_app as app

from quart import views

from tsundoku.manager import Entry
from .response import APIResponse

logger = logging.getLogger("tsundoku")


class EntriesAPI(views.MethodView):
    async def get(self, entry_id: int) -> APIResponse:
        async with app.acquire_db() as con:
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
            return APIResponse(
                status=404, error="Entry with specified ID does not exist."
            )

        return APIResponse(result=Entry(app, entry).to_dict())
