from collections.abc import Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

import aiohttp

from .kitsu import API_URL
from .show import Show


@dataclass
class ShowCollection:
    _shows: list[Show]

    def __len__(self) -> int:
        return len(self._shows)

    def __iter__(self) -> Generator[Show, None, None]:
        yield from self._shows

    def to_list(self) -> list[dict]:
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
    async def all(cls, app: TsundokuApp) -> "ShowCollection":
        """
        Retrieves a collection of all Show
        objects presently stored in the database.

        Returns
        -------
        ShowCollection
            Collection of all shows.
        """
        async with app.acquire_db() as con:
            shows = await con.fetchall(
                """
                SELECT
                    s.id as id_,
                    s.library_id,
                    s.title,
                    s.title_local,
                    s.desired_format,
                    s.season,
                    s.episode_offset,
                    s.watch,
                    s.post_process,
                    s.preferred_resolution,
                    s.preferred_release_group,
                    s.created_at,
                    ki.kitsu_id,
                    ki.slug,
                    ki.show_status,
                    ki.cached_poster_url
                FROM
                    shows as s
                LEFT JOIN
                    kitsu_info as ki
                ON s.id = ki.show_id
                ORDER BY title;
            """
            )

        shows_ = [await Show.from_data(app, show) for show in shows]
        return cls(_shows=shows_)

    async def gather_statuses(self) -> None:
        """
        Gathers the status for all of the shows
        in the collection.

        The status is an attribute that is assigned
        on each Show's metadata object.
        """
        managers = [s.metadata for s in self._shows if await s.metadata.should_update_status()]

        if not managers:
            return

        status_map: dict[int, str] = {}
        async with aiohttp.ClientSession() as sess:
            payload = {
                "filter[id]": ",".join(map(str, [m.kitsu_id for m in managers])),
                "fields[anime]": "status",
            }
            async with sess.get(API_URL, params=payload) as resp:
                data = await resp.json()
                for show in data.get("data", []):
                    show_id = int(show["id"])
                    status = show.get("attributes", {}).get("status", None)
                    status_map[show_id] = status

        for manager in managers:
            if manager.kitsu_id is not None and manager.kitsu_id in status_map:
                await manager.set_status(status_map[manager.kitsu_id])
