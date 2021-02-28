from typing import List, Optional, Union

from quart import request, views
from quart import current_app as app

from .response import APIResponse
from tsundoku.feeds.entry import Entry


class EntriesAPI(views.MethodView):
    def _doc_get_0(self) -> None:
        """
        Retrieves all entries for a specified show.

        .. :quickref: Entries; Retrieve all entries.

        :status 200: entries found

        :returns: List[:class:`dict`]
        """

    def _doc_get_1(self) -> None:
        """
        Retrieves a single entry based on its ID.

        .. :quickref: Entries; Retrieve an entry.

        :status 200: entry found
        :status 404: entry with passed id not found

        :returns: :class:`dict`
        """

    async def get(self, show_id: int, entry_id: Optional[int]) -> APIResponse:
        """
        Retrieve all entries or a single entry
        for a specified show.

        Returns
        -------
        Union[dict, List[dict]]
            A dict or a list of dict containing
            the requested entry information.
        """
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

            return APIResponse(
                result=[dict(record) for record in entries]
            )
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
                return APIResponse(
                    status=404,
                    error="Entry with specified ID does not exist."
                )

            return APIResponse(
                result=dict(entry)
            )


    async def post(self, show_id: int, entry_id: int=None) -> APIResponse:
        """
        Manually begins handling of an entry for a specified show.
        Handling involves downloading, moving, and renaming.

        If an empty string is passed for a magnet URL, nothing will
        be downloaded and the entry will be marked as complete.

        .. :quickref: Entries; Add an entry.

        :status 200: entry added successfully
        :status 400: invalid arguments

        :form integer episode: the entry's episode
        :form string magnet: the entry's magnet url

        :returns: :class:`dict`
        """
        required_arguments = {"episode", "magnet"}
        await request.get_data()
        arguments = await request.form

        if set(arguments.keys()) != required_arguments:
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

        return APIResponse(
            result=dict(new_entry)
        )


    async def delete(self, show_id: int, entry_id: int) -> APIResponse:
        """
        Deletes a single entry from a show.

        .. :quickref: Entries; Delete an entry.

        :status 200: entry successfully deleted
        :status 404: entry with passed id not found

        :returns: :class:`bool`
        """
        async with app.db_pool.acquire() as con:
            deleted = await con.fetchval("""
                DELETE FROM
                    show_entry
                WHERE id=$1
                RETURNING id;
            """, entry_id)

        if deleted:
            return APIResponse(
                result=True
            )
        else:
            return APIResponse(
                status=404,
                error="Entry with specified ID does not exist."
            )
