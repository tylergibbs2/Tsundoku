import json
import typing

from quart import Response, request, views
from quart import current_app as app


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