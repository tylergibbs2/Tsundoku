import logging
from typing import Optional

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
    "upcoming": "<span class='img-overlay-span tag is-primary'>Upcoming</span>"
}


class ShowsAPI(views.MethodView):
    def _doc_get_0(self) -> None:
        """
        Retrieves a list of all shows stored in the database.

        .. :quickref: Shows; Retrieve all shows.

        :status 200: shows found

        :returns: List[:class:`dict`]
        """

    def _doc_get_1(self) -> None:
        """
        Retrieves a single show based on its ID.

        .. :quickref: Shows; Retrieve a show.

        :status 200: the show found
        :status 404: show with passed id not found

        :returns: :class:`dict`
        """

    async def get(self, show_id: Optional[int]) -> APIResponse:
        """
        get_0: without the `show_id` argument.
        get_1: with the `show_id` argument.
        """
        if show_id is None:
            shows = await ShowCollection.all()
            await shows.gather_statuses()

            return APIResponse(
                result=shows.to_list()
            )
        else:
            show = await Show.from_id(show_id)

            return APIResponse(
                result=show.to_dict()
            )

    async def post(self, show_id: None) -> APIResponse:
        """
        Adds a new show to the database.

        .. :quickref: Shows; Add a new show.

        :status 200: show added successfully
        :status 400: bad or missing arguments
        :status 500: unexpected server error

        :form string title: the new show's title
        :form string desired_format: the new show's desired file format
        :form string desired_folder: the new show's target folder for moving
        :form integer season: the season to use when naming the show
        :form integer episode_offset: the episode offset to use when renaming (default :code:`0`)

        :returns: :class:`dict`
        """
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
            return APIResponse(
                status=400,
                error="Missing season argument."
            )

        try:
            season = int(season)
        except ValueError:
            return APIResponse(
                status=400,
                error="Season is not an integer."
            )

        episode_offset = arguments.get("episode_offset")
        if episode_offset is None:
            episode_offset = 0
        else:
            try:
                episode_offset = int(episode_offset)
            except ValueError:
                return APIResponse(
                    status=400,
                    error="Episode offset is not an integer."
                )

        show = await Show.insert(
            title=arguments["title"],
            desired_format=desired_format,
            desired_folder=desired_folder,
            season=season,
            episode_offset=episode_offset
        )

        async with app.acquire_db() as con:
            await con.execute("""
                INSERT OR IGNORE INTO
                    webhook
                    (show_id, base)
                SELECT (?), id FROM webhook_base;
            """, show.id_)

        logger.info("New Show Added - Preparing to Check for New Releases")
        app.poller.reset_rss_cache()
        await app.poller.poll()

        show = await Show.from_id(show.id_)

        return APIResponse(
            result=show.to_dict()
        )

    async def put(self, show_id: int) -> APIResponse:
        """
        Updates a specified show using the given parameters.

        .. :quickref: Shows; Update an existing show.

        :status 200: show updated successfully
        :status 500: unexpected server error

        :form string title: the new title
        :form string desired_format: the new desired format
        :form string desired_folder: the new desired folder
        :form integer season: the new season
        :form integer episode_offset: the new episode offset

        :returns: :class:`dict`
        """
        arguments = await request.get_json()

        desired_format = arguments.get("desired_format")
        if not desired_format:
            desired_format = None

        desired_folder = arguments.get("desired_folder")
        if not desired_folder:
            desired_folder = None

        season = int(arguments["season"])
        episode_offset = int(arguments["episode_offset"])

        show = await Show.from_id(show_id)
        do_poll = False

        old_title = show.title
        old_kitsu = show.metadata.kitsu_id

        if old_title != arguments["title"]:
            do_poll = True
            await show.metadata.fetch(show_id, arguments["title"])

        try:
            new_kitsu = int(arguments["kitsu_id"])
            if old_kitsu != new_kitsu:
                await show.metadata.fetch_by_kitsu(show_id, new_kitsu)
        except (KeyError, ValueError):
            pass

        show.title = arguments["title"]
        show.desired_format = desired_format
        show.desired_folder = desired_folder
        show.season = season
        show.episode_offset = episode_offset

        await show.update()

        if do_poll:
            logger.info("Existing Show Updated - Preparing to Check for New Releases")
            app.poller.reset_rss_cache()
            await app.poller.poll()

        show = await Show.from_id(show_id)

        return APIResponse(
            result=show.to_dict()
        )

    async def delete(self, show_id: int) -> APIResponse:
        """
        Deletes a show with the specified ID.

        This will delete all entries of that show as well.

        .. :quickref: Shows; Delete a show.

        :status 200: deletion request received

        :returns: :class:`bool`
        """
        async with app.acquire_db() as con:
            await con.execute("""
                DELETE FROM
                    shows
                WHERE id=?;
            """, show_id)

        return APIResponse(
            result=True
        )
