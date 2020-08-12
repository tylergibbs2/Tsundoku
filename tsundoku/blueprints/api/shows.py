import json
from typing import List, Union

from quart import abort, request, views
from quart import current_app as app
from quart_auth import current_user

from tsundoku import kitsu


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
        if not await current_user.is_authenticated:
            return abort(401, "You are not authorized to access this resource.")

        if show_id is None:
            async with app.db_pool.acquire() as con:
                shows = await con.fetch("""
                    SELECT id, title, desired_format, desired_folder,
                    season, episode_offset, show_image FROM shows;
                """)

                return json.dumps([dict(record) for record in shows])
        else:
            async with app.db_pool.acquire() as con:
                show = await con.fetchrow("""
                    SELECT id, title, desired_format, desired_folder,
                    season, episode_offset, show_image FROM shows WHERE id=$1;
                """, show_id)

            if not show:
                show = {}

            return json.dumps(dict(show))


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
        if not await current_user.is_authenticated:
            return abort(401, "You are not authorized to access this resource.")

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

        kitsu_id = await kitsu.get_id(arguments["title"])

        async with app.db_pool.acquire() as con:
            await con.execute("""
                INSERT INTO shows (title, desired_format, desired_folder,
                season, episode_offset, kitsu_id) VALUES ($1, $2, $3, $4, $5, $6);
            """, arguments["title"], desired_format, desired_folder, season,
            episode_offset, kitsu_id)

        return json.dumps({"success": True})


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
        if not await current_user.is_authenticated:
            return abort(401, "You are not authorized to access this resource.")

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
            og_data = await con.fetchrow("""
                SELECT title, kitsu_id FROM shows WHERE id=$1;
            """, show_id)
            if arguments["title"] != og_data["title"]:
                kitsu_id = await kitsu.get_id(arguments["title"])
            elif int(arguments["kitsu_id"]) != og_data["kitsu_id"]:
                kitsu_id = int(arguments["kitsu_id"])
                await con.execute("""
                    UPDATE shows SET cached_poster_url=NULL where id=$1;
                """, show_id)
            else:
                kitsu_id = og_data["kitsu_id"]

            await con.execute("""
                UPDATE shows SET title=$1, desired_format=$2, desired_folder=$3,
                season=$4, episode_offset=$5, kitsu_id=$6 WHERE id=$7;
            """, arguments["title"], desired_format, desired_folder, season,
            episode_offset, kitsu_id, show_id)

        return json.dumps({"success": True})


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
        if not await current_user.is_authenticated:
            return abort(401, "You are not authorized to access this resource.")

        async with app.db_pool.acquire() as con:
            await con.execute("""
                DELETE FROM show_entry WHERE show_id=$1;
            """, show_id)
            await con.execute("""
                DELETE FROM shows WHERE id=$1;
            """, show_id)

        return json.dumps({"success": True})
