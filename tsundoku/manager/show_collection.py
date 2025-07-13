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
    async def all(cls, app: "TsundokuApp") -> "ShowCollection":
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

    @classmethod
    async def filtered_paginated(cls, app: "TsundokuApp", statuses: list[str], limit: int = 17, offset: int = 0, text_filter: str | None = None, sort_key: str = "title", sort_direction: str = "+") -> tuple["ShowCollection", int]:
        """
        Retrieves a paginated collection of Show objects filtered by status, text, and sorted.
        """
        # Build WHERE clause
        if statuses:
            where_clauses = ["ki.show_status IS NOT NULL", "ki.show_status IN ({})".format(",".join(["?"] * len(statuses)))]
            params = list(statuses)
        else:
            # If no statuses are selected, return no shows
            return cls(_shows=[]), 0
        if text_filter:
            where_clauses.append("(LOWER(s.title) LIKE ? OR LOWER(s.title_local) LIKE ?)")
            like_val = f"%{text_filter.lower()}%"
            params.extend([like_val, like_val])
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        # Sorting
        if sort_key == "title":
            order_sql = f"ORDER BY LOWER(s.title) {'ASC' if sort_direction == '+' else 'DESC'}"
        elif sort_key == "dateAdded":
            order_sql = f"ORDER BY s.created_at {'ASC' if sort_direction == '+' else 'DESC'}"
        elif sort_key == "update":
            order_sql = f"ORDER BY last_update {'ASC' if sort_direction == '+' else 'DESC'}"
        else:
            order_sql = "ORDER BY s.title ASC"
        # For last_update, join show_entry and use MAX
        join_last_update = ""
        select_last_update = ""
        group_by = ""
        if sort_key == "update":
            join_last_update = "LEFT JOIN show_entry se ON s.id = se.show_id"
            select_last_update = ", MAX(se.last_update) as last_update"
            group_by = "GROUP BY s.id"
        async with app.acquire_db() as con:
            id_rows = await con.fetchall(
                f"""
                SELECT DISTINCT s.id FROM shows as s
                LEFT JOIN kitsu_info as ki ON s.id = ki.show_id
                {join_last_update}
                WHERE {where_sql}
                {group_by}
                {order_sql}
                """,
                *params,
            )
            all_ids = [row[0] for row in id_rows]
            total_count = len(all_ids)
            paged_ids = all_ids[offset : offset + limit]
            if not paged_ids:
                return cls(_shows=[]), total_count
            # Now fetch the actual show data for these IDs
            shows = await con.fetchall(
                f"""
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
                    {select_last_update}
                FROM
                    shows as s
                LEFT JOIN
                    kitsu_info as ki
                ON s.id = ki.show_id
                {join_last_update}
                WHERE s.id IN ({",".join(["?"] * len(paged_ids))})
                {group_by}
                {order_sql}
                """,
                *paged_ids,
            )

        shows_ = [await Show.from_data(app, show) for show in shows]
        return cls(_shows=shows_), total_count

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
