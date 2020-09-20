import json
from typing import List, Union

from quart import abort, Response, request, views
from quart import current_app as app
from quart_auth import current_user

from tsundoku.feeds.entry import Entry


class EntriesAPI(views.MethodView):
    async def get(self, show_id: int, entry_id: int=None) -> Union[dict, List[dict]]:
        """
        Retrieve all entries or a single entry
        for a specified show.

        Returns
        -------
        Union[dict, List[dict]]
            A dict or a list of dict containing
            the requested entry information.
        """
        if not await current_user.is_authenticated:
            return abort(401, "You are not authorized to access this resource.")

        if entry_id is None:
            async with app.db_pool.acquire() as con:
                entries = await con.fetch("""
                    SELECT
                        id,
                        episode,
                        current_state,
                        torrent_hash
                    FROM
                        show_entry
                    WHERE show_id=$1;
                """, show_id)

            return json.dumps([dict(record) for record in entries])
        else:
            async with app.db_pool.acquire() as con:
                entry = await con.fetchrow("""
                    SELECT
                        id,
                        episode,
                        current_state,
                        torrent_hash
                    FROM
                        show_entry
                    WHERE show_id=$1 AND id=$2;
                """, show_id, entry_id)

            if entry is None:
                entry = {}

            return json.dumps(dict(entry))


    async def post(self, show_id: int, entry_id: int=None):
        """
        Manually begins handling of an entry for
        a specified show. Handling involves downloading,
        moving, and renaming.

        If an empty string is passed for a magnet URL,
        nothing will be downloaded and the entry will
        be marked as complete.

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
        if not await current_user.is_authenticated:
            return abort(401, "You are not authorized to access this resource.")

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

        if arguments["magnet"]:
            entry_id = await app.downloader.begin_handling(show_id, episode, arguments["magnet"])
        else:
            async with app.db_pool.acquire() as con:
                entry_id = await con.fetchval("""
                    INSERT INTO
                        show_entry (show_id, episode, current_state, torrent_hash)
                    VALUES
                        ($1, $2, $3, $4)
                    RETURNING id;
                """, show_id, episode, "completed", "")

        async with app.db_pool.acquire() as con:
            new_entry = await con.fetchrow("""
                SELECT
                    id,
                    show_id,
                    episode,
                    current_state,
                    torrent_hash,
                    file_path
                FROM
                    show_entry
                WHERE id=$1;
            """, entry_id)

        entry = Entry(app, new_entry)
        await entry._handle_webhooks()

        response["success"] = True
        response["entry"] = dict(new_entry)

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
        if not await current_user.is_authenticated:
            return abort(401, "You are not authorized to access this resource.")

        async with app.db_pool.acquire() as con:
            await con.execute("""
                DELETE FROM
                    show_entry
                WHERE id=$1;
            """, entry_id)

        return json.dumps({"success": True})
