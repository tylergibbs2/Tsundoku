import logging
from typing import List, Union

from quart import request, views
from quart import current_app as app

from .response import APIResponse
from tsundoku.kitsu import KitsuManager


logger = logging.getLogger("tsundoku")


class ShowsAPI(views.MethodView):
    async def get(self, show_id: int=None) -> Union[dict, List[dict]]:
        """
        Can retrieve either a list of all rows in
        the shows table, or a single row given a show
        ID.

        Returns
        -------
        Union[dict, List[dict]]
            A dict or a list of dict containing
            the requested show information.
        """
        if show_id is None:
            async with app.db_pool.acquire() as con:
                shows = await con.fetch("""
                    SELECT
                        id,
                        title,
                        desired_format,
                        desired_folder,
                        season,
                        episode_offset
                    FROM
                        shows;
                """)

                return APIResponse(
                    result=[dict(record) for record in shows]
                )
        else:
            async with app.db_pool.acquire() as con:
                show = await con.fetchrow("""
                    SELECT
                        id,
                        title,
                        desired_format,
                        desired_folder,
                        season,
                        episode_offset
                    FROM
                        shows
                    WHERE id=$1;
                """, show_id)

            if not show:
                return APIResponse(
                    status=404,
                    error="Show with specified ID does not exist."
                )

            return APIResponse(
                result=dict(show)
            )


    async def post(self, show_id: int=None) -> dict:
        """
        Creates a show row in the shows table.

        Parameters
        ----------
        title: str
            The title.
        desired_format: str
            The file format.
        desired_folder: str
            The final move location.
        season: int
            The season.
        episode_offset: int
            The episode offset.

        Returns
        -------
        dict
            Single key: `success`. Value is True if success,
            False otherwise.
        """
        await request.get_data()
        arguments = await request.form

        if not arguments["desired_format"]:
            desired_format = None
        else:
            desired_format = arguments["desired_format"]

        if not arguments["desired_folder"]:
            desired_folder = None
        else:
            desired_folder = arguments["desired_folder"]

        season = int(arguments["season"])
        episode_offset = int(arguments["episode_offset"])

        async with app.db_pool.acquire() as con:
            new_id = await con.fetchval("""
                INSERT INTO
                    shows
                    (title, desired_format, desired_folder,
                    season, episode_offset)
                VALUES
                    ($1, $2, $3, $4, $5)
                RETURNING id;
            """, arguments["title"], desired_format, desired_folder, season,
            episode_offset)

            await con.execute("""
                INSERT INTO
                    webhook
                    (show_id, base)
                SELECT ($1), id FROM webhook_base
                ON CONFLICT DO NOTHING;
            """, new_id)

        await KitsuManager.fetch(new_id, arguments["title"])

        logger.info("New Show Added - Preparing to Check for New Releases")
        for parser in app.rss_parsers:
            feed = await app.poller.get_feed_from_parser(parser)

            logger.info(f"{parser.name} - Checking for New Releases...")
            await app.poller.check_feed(feed)
            logger.info(f"{parser.name} - Checked for New Releases")

        async with app.db_pool.acquire() as con:
            new_show = await con.fetchrow("""
                SELECT
                    id,
                    title,
                    desired_format,
                    desired_folder,
                    season,
                    episode_offset
                FROM
                    shows
                WHERE id=$1;
            """, new_id)

        if new_show:
            return APIResponse(
                result=dict(new_show)
            )
        else:
            return APIResponse(
                status=500,
                error="The server failed to add the new Show."
            )


    async def put(self, show_id: int) -> dict:
        """
        Updates a specified show in the shows table
        using the given parameters.

        Parameters
        ----------
        title: str
            The updated title.
        desired_format: str
            The updated file format.
        desired_folder: str
            The updated final move location.
        season: int
            The updated season.
        episode_offset: int
            The updated episode offset.

        Returns
        -------
        dict
            Single key: `success`. Value is True if success,
            False otherwise.
        """
        await request.get_data()
        arguments = await request.form

        if not arguments["desired_format"]:
            desired_format = None
        else:
            desired_format = arguments["desired_format"]

        if not arguments["desired_folder"]:
            desired_folder = None
        else:
            desired_folder = arguments["desired_folder"]

        season = int(arguments["season"])
        episode_offset = int(arguments["episode_offset"])

        async with app.db_pool.acquire() as con:
            old_title = await con.fetchval("""
                SELECT
                    title
                FROM
                    shows
                WHERE id=$1;
            """, show_id)

            if old_title != arguments["title"]:
                await KitsuManager.fetch(show_id, arguments["title"])

            old_kitsu = await con.fetchval("""
                SELECT
                    kitsu_id
                FROM
                    kitsu_info
                WHERE
                    show_id=$1;
            """, show_id)

            try:
                new_kitsu = int(arguments["kitsu_id"])
                if old_kitsu != new_kitsu:
                    await KitsuManager.fetch_by_kitsu(show_id, new_kitsu)
            except ValueError:
                pass

            await con.execute("""
                UPDATE
                    shows
                SET
                    title=$1,
                    desired_format=$2,
                    desired_folder=$3,
                    season=$4,
                    episode_offset=$5
                WHERE id=$6;
            """, arguments["title"], desired_format, desired_folder, season,
            episode_offset, show_id)

        logger.info("Existing Show Updated - Preparing to Check for New Releases")
        for parser in app.rss_parsers:
            feed = await app.poller.get_feed_from_parser(parser)

            logger.info(f"{parser.name} - Checking for New Releases...")
            await app.poller.check_feed(feed)
            logger.info(f"{parser.name} - Checked for New Releases")

        async with app.db_pool.acquire() as con:
            new_show = await con.fetchrow("""
                SELECT
                    id,
                    title,
                    desired_format,
                    desired_folder,
                    season,
                    episode_offset
                FROM
                    shows
                WHERE id=$1;
            """, show_id)

        if new_show:
            return APIResponse(
                result=dict(new_show)
            )
        else:
            return APIResponse(
                status=500,
                error="The server failed to update the existing Show."
            )


    async def delete(self, show_id: int) -> dict:
        """
        Deletes a show with specified ID from the
        shows table.

        This will delete all entries of that show as well.

        Returns
        -------
        dict
            Single key: `success`. Value is True if success,
            False otherwise.
        """
        async with app.db_pool.acquire() as con:
            deleted = await con.fetchval("""
                DELETE FROM
                    shows
                WHERE id=$1
                RETURNING id;
            """, show_id)

        if deleted:
            return APIResponse(
                result=True
            )
        else:
            return APIResponse(
                status=404,
                error="Show with specified ID does not exist."
            )
