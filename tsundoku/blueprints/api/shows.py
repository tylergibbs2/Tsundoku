from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp
    app: TsundokuApp
else:
    from quart import current_app as app


from quart import request, views

from tsundoku.manager import Show, ShowCollection

from .response import APIResponse

logger = logging.getLogger("tsundoku")


status_html_map = {
    "current": "<span class='img-overlay-span tag is-success'>Airing</span>",
    "finished": "<span class='img-overlay-span tag is-danger'>Finished</span>",
    "tba": "<span class='img-overlay-span tag is-warning'>TBA</span>",
    "unreleased": "<span class='img-overlay-span tag is-info'>Unreleased</span>",
    "upcoming": "<span class='img-overlay-span tag is-primary'>Upcoming</span>",
}


class ShowsAPI(views.MethodView):
    async def get(self, show_id: Optional[int]) -> APIResponse:
        if show_id is None:
            shows = await ShowCollection.all()
            await shows.gather_statuses()

            return APIResponse(result=shows.to_list())
        else:
            try:
                show = await Show.from_id(show_id)
            except Exception:
                return APIResponse(status=404, error="Show with passed ID not found.")

            return APIResponse(result=show.to_dict())

    async def post(self, show_id: None) -> APIResponse:
        # show_id here will always be None. Having it as a parameter
        # is required due to how the defaults are handled with GET
        # and POST methods on the routing table.
        arguments = await request.get_json()

        # patch for ajax call
        if not arguments:
            await request.get_data()
            arguments = await request.form

        desired_format = arguments.get("desired_format")
        desired_folder = arguments.get("desired_folder")

        season = arguments.get("season")
        if season is None:
            return APIResponse(status=400, error="Missing season argument.")

        try:
            season = int(season)
        except ValueError:
            return APIResponse(status=400, error="Season is not an integer.")

        episode_offset = arguments.get("episode_offset")
        if episode_offset is None:
            episode_offset = 0
        else:
            try:
                episode_offset = int(episode_offset)
            except ValueError:
                return APIResponse(
                    status=400, error="Episode offset is not an integer."
                )

        show = await Show.insert(
            title=arguments["title"],
            desired_format=desired_format,
            desired_folder=desired_folder,
            season=season,
            episode_offset=episode_offset,
            watch=arguments.get("watch", True),
            post_process=arguments.get("post_process", True),
        )

        async with app.acquire_db() as con:
            await con.execute(
                """
                INSERT OR IGNORE INTO
                    webhook
                    (show_id, base)
                SELECT (?), id FROM webhook_base;
            """,
                show.id_,
            )

        logger.info(
            f"New Show Added, <s{show.id_}> - Preparing to Check for New Releases"
        )
        app.poller.reset_rss_cache()
        await app.poller.poll()

        show = await Show.from_id(show.id_)

        return APIResponse(result=show.to_dict())

    async def put(self, show_id: int) -> APIResponse:
        arguments = await request.get_json()

        try:
            show = await Show.from_id(show_id)
        except Exception:
            return APIResponse(status=404, error="Show with passed ID not found.")

        desired_format = arguments.get("desired_format")
        if not desired_format:
            show.desired_format = ""
        else:
            show.desired_format = desired_format

        desired_folder = arguments.get("desired_folder")
        if not desired_folder:
            show.desired_folder = ""
        else:
            show.desired_folder = desired_folder

        if "season" in arguments:
            try:
                season = int(arguments["season"])
            except Exception:
                return APIResponse(status=400, error="Season is not a valid integer.")

            show.season = season

        if "episode_offset" in arguments:
            try:
                episode_offset = int(arguments["episode_offset"])
            except Exception:
                return APIResponse(
                    status=400, error="Episode offset is not a valid integer."
                )

            show.episode_offset = episode_offset

        do_poll = False

        old_title = show.title
        old_kitsu = show.metadata.kitsu_id

        if old_title != arguments["title"]:
            do_poll = True
            await show.metadata.fetch(show_id, arguments["title"])

        if "kitsu_id" in arguments:
            try:
                new_kitsu = int(arguments["kitsu_id"])
            except Exception:
                return APIResponse(status=400, error="Kitsu ID is not a valid integer.")

            if old_kitsu != new_kitsu:
                await show.metadata.fetch_by_kitsu(show_id, new_kitsu)

        if arguments.get("title"):
            show.title = arguments["title"]

        if "watch" in arguments:
            if not isinstance(arguments["watch"], bool):
                return APIResponse(status=400, error="Watch is not a valid boolean.")

            show.watch = arguments["watch"]

        if "post_process" in arguments:
            if not isinstance(arguments["post_process"], bool):
                return APIResponse(
                    status=400, error="Post process is not a valid boolean."
                )

            show.post_process = arguments["post_process"]

        await show.update()

        if do_poll:
            logger.info(
                f"Existing Show Updated, <s{show_id}> - Preparing to Check for New Releases"
            )
            app.poller.reset_rss_cache()
            await app.poller.poll()

        show = await Show.from_id(show_id)

        return APIResponse(result=show.to_dict())

    async def delete(self, show_id: int) -> APIResponse:
        """
        Deletes a show with the specified ID.

        This will delete all entries of that show as well.

        .. :quickref: Shows; Delete a show.

        :status 200: deletion request received

        :returns: :class:`bool`
        """
        async with app.acquire_db() as con:
            await con.execute(
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

            title = await con.fetchval()

            await con.execute(
                """
                DELETE FROM
                    shows
                WHERE id=?;
            """,
                show_id,
            )

        logger.info(f"Show Deleted - {title}")

        return APIResponse(result=True)
