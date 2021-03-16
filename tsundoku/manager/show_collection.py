from __future__ import annotations

from dataclasses import dataclass
from typing import List

import aiohttp
from quart import current_app as app

from .kitsu import API_URL
from .show import Show


@dataclass
class ShowCollection:
    _shows: List[Show]

    def to_list(self) -> List[dict]:
        """
        Serializes all of the Shows in the collection
        to a list.

        Returns
        -------
        List[dict]
            List of serialized Shows.
        """
        return [s.to_dict() for s in self._shows]

    @classmethod
    async def all(cls) -> ShowCollection:
        """
        Retrieves a collection of all Show
        objects presently stored in the database.

        Returns
        -------
        ShowCollection
            Collection of all shows.
        """
        async with app.db_pool.acquire() as con:
            shows = await con.fetch("""
                SELECT
                    id
                FROM
                    shows;
            """)

        _shows = [await Show.from_id(show["id"]) for show in shows]
        instance = cls(
            _shows=_shows
        )
        return instance

    async def gather_statuses(self) -> None:
        """
        Gathers the status for all of the shows
        in the collection.

        The status is an attribute that is assigned
        on each Show's metadata object.
        """
        managers = [s.metadata for s in self._shows]
        to_retrieve: List[int] = []

        for manager in managers:
            if manager.kitsu_id is not None:
                to_retrieve.append(manager.kitsu_id)

        async with aiohttp.ClientSession() as sess:
            payload = {
                "filter[id]": ",".join(map(str, to_retrieve)),
                "fields[anime]": "status"
            }
            async with sess.get(API_URL, params=payload) as resp:
                data = await resp.json()
                for i in range(len(to_retrieve)):
                    try:
                        show_response: dict = data["data"][i]
                        status = show_response.get("attributes", {}).get("status", None)
                        managers[i].status = status
                    except IndexError:
                        pass
