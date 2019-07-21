import json
import typing

from quart import Blueprint, Response, request, views
from quart import current_app as app

api_blueprint = Blueprint('api', __name__, url_prefix="/api")


class ShowsAPI(views.MethodView):

    async def get(self, show_id: int=None) -> typing.Union[dict, typing.List[dict]]:
        """
        Can retrieve either a list of all rows in
        the shows table, or a single row given a show
        ID.

        Returns
        -------
        typing.Union[dict, typing.List[dict]]
            A dict or a list of dict containing
            the requested show information.
        """
        if show_id is None:
            async with app.db_pool.acquire() as con:
                shows = await con.fetch("""
                    SELECT id, title, desired_format, desired_folder,
                    season, episode_offset FROM shows;
                """)

                return json.dumps([dict(record) for record in shows])   
        else:
            async with app.db_pool.acquire() as con:
                show = await con.fetchrow("""
                    SELECT id, title, desired_format, desired_folder,
                    season, episode_offset FROM shows WHERE id=$1;
                """, show_id)

            if not show:
                show = {}

            return json.dumps(dict(show))


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
            await con.execute("""
                UPDATE shows SET title=$1, desired_format=$2, desired_folder=$3,
                season=$4, episode_offset=$5 WHERE id=$6;
            """, arguments["title"], desired_format, desired_folder, season,
            episode_offset, show_id)

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
        async with app.db_pool.acquire() as con:
            await con.execute("""
                DELETE FROM show_entry WHERE show_id=$1;
            """, show_id)
            await con.execute("""
                DELETE FROM shows WHERE id=$1;
            """, show_id)

        return json.dumps({"success": True})


class EntriesAPI(views.MethodView):
    async def get(self, show_id: int, entry_id: int=None) -> typing.Union[dict, typing.List[dict]]:
        """
        Retrieve all entries or a single entry
        for a specified show.

        Returns
        -------
        typing.Union[dict, typing.List[dict]]
            A dict or a list of dict containing
            the requested entry information.
        """
        if entry_id is None:
            async with app.db_pool.acquire() as con:
                entries = await con.fetch("""
                    SELECT id, episode, current_state, torrent_hash
                    FROM show_entry WHERE show_id=$1;
                """, show_id)

            return json.dumps([dict(record) for record in entries])   
        else:
            async with app.db_pool.acquire() as con:
                entry = await con.fetchrow("""
                    SELECT id, episode, current_state, torrent_hash
                    FROM show_entry WHERE show_id=$1 AND id=$2;
                """, show_id, entry_id)

            if entry is None:
                entry = {}

            return json.dumps(dict(entry))

    
    async def post(self, show_id: int):
        """
        Manually begins handling of an entry for
        a specified show. Handling involves downloading,
        moving, and renaming.

        Parameters
        ----------
        episode: int
            The episode to handle.
        magnet: str
            The magnet URL for the entry's
            torrent.

        Returns
        -------
        dict
            Single key: `success`. Value is True if success,
            False otherwise.
        """
        required_arguments = {"episode", "magnet"}
        await request.get_data()
        arguments = await request.form

        response = {"success": False}

        if set(arguments.keys()) != required_arguments:
            response["error"] = "too many arguments or missing required argument"
            return Response(json.dumps(response), status=400)
        
        try:
            episode = int(arguments["episode"])
        except ValueError:
            response["error"] = "episode argument must be int"
            return Response(json.dumps(response), status=400)

        await app.downloader.begin_handling(show_id, episode, arguments["magnet"])
        response["success"] = True

        return json.dumps(response)

    
    async def delete(self, show_id: int, entry_id: int):
        """
        Deletes a single entry from a show.

        Returns
        -------
        dict
            Single key: `success`. Value is True if success,
            False otherwise.
        """
        async with app.db_pool.acquire() as con:
            await con.execute("""
                DELETE FROM show_entry WHERE id=$1;
            """, entry_id)

        return json.dumps({"success": True})
        

def setup_views():
    # Setup ShowsAPI URL rules.
    shows_view = ShowsAPI.as_view("shows_api")

    api_blueprint.add_url_rule(
        "/shows/",
        defaults={
            "show_id": None
        },
        view_func=shows_view,
        methods=["GET"]
    )
    api_blueprint.add_url_rule(
        "/shows/<int:show_id>",
        view_func=shows_view,
        methods=["GET", "PUT", "DELETE"]
    )

    # Setup EntriesAPI URL rules.
    entries_view = EntriesAPI.as_view("entries_api")

    api_blueprint.add_url_rule(
        "/shows/<int:show_id>/entries/",
        defaults={
            "entry_id": None
        },
        view_func=entries_view,
        methods=["GET"]
    )
    api_blueprint.add_url_rule(
        "/shows/<int:show_id>/entries/<int:entry_id>",
        view_func=entries_view,
        methods=["GET", "POST", "DELETE"]
    )

setup_views()
