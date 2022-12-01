import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

    app: TsundokuApp
else:
    from quart import current_app as app

from quart import request, views

from tsundoku.nyaa import NyaaSearcher, SearchResult

from .response import APIResponse

logger = logging.getLogger("tsundoku")


class NyaaAPI(views.MethodView):
    async def get(self) -> APIResponse:
        query = request.args.get("query")
        if not query:
            return APIResponse(result=[])

        try:
            results = await NyaaSearcher.search(app, query)
        except Exception as e:
            logger.error(f"Nyaa API - Search Error: {e}")
            return APIResponse(
                status=400, error="Error searching for the specified query."
            )

        return APIResponse(result=[sr.to_dict() for sr in results])

    async def post(self) -> APIResponse:
        arguments = await request.get_json()

        show_id = arguments.get("show_id")
        torrent_link = arguments.get("torrent_link")
        overwrite = arguments.get("overwrite")

        if not show_id or not torrent_link:
            return APIResponse(status=400, error="Missing required parameters.")

        try:
            show_id = int(show_id)
        except ValueError:
            return APIResponse(status=400, error="Show ID passed is not an integer.")

        async with app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    id
                FROM
                    shows
                WHERE id=?;
            """,
                show_id,
            )
            show_id = await con.fetchval()

        if not show_id:
            return APIResponse(
                status=404, error="Show ID does not exist in the database."
            )

        search_result = SearchResult.from_necessary(app, show_id, torrent_link)

        logger.info(f"Processing new search result for Show <s{show_id}>")

        entries = await search_result.process(overwrite=overwrite)

        return APIResponse(result=[e.to_dict() for e in entries])
