from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

from tsundoku.constants import VALID_RESOLUTIONS
from tsundoku.utils import normalize_resolution, compare_version_strings, ParserResult

logger = logging.getLogger("tsundoku")


@dataclass
class SeenRelease:
    app: TsundokuApp

    title: str
    release_group: str
    episode: int
    resolution: str
    version: str
    torrent_destination: str
    seen_at: datetime

    def to_dict(self) -> dict:
        """
        Returns the SeenRelease object as a dictionary.

        Returns
        -------
        dict
            The serialized Entry object.
        """
        return {
            "title": self.title,
            "release_group": self.release_group,
            "episode": self.episode,
            "resolution": self.resolution,
            "version": self.version,
            "torrent_destination": self.torrent_destination,
            "seen_at": self.seen_at.isoformat(),
        }

    @classmethod
    async def distinct(
        cls,
        app: TsundokuApp,
        field: str,
        /,
        title: Optional[str] = None,
        release_group: Optional[str] = None,
        resolution: Optional[str] = None,
    ) -> list[str]:
        """
        Gets a distinct field with optional filtering.

        Parameters
        ----------
        field : str
            The field to get distinct values for. One of "title", "release_group", "resolution".
        title : Optional[str]
            The title to filter by.
        release_group : Optional[str]
            The release group to filter by.
        resolution : Optional[str]
            The resolution to filter by.

        Returns
        -------
        list[str]
            All distinct values of the passed field.
        """
        if field not in ("title", "release_group", "resolution"):
            raise ValueError(f"Invalid field '{field}'.")

        parameters = [p for p in (title, release_group, resolution) if p is not None]
        conditions = []
        if title is not None:
            conditions.append("title = ?")
        if release_group is not None:
            conditions.append("release_group = ?")
        if resolution is not None:
            conditions.append("resolution = ?")

        async with app.acquire_db() as con:
            rows = await con.fetchall(
                f"""
                SELECT DISTINCT
                    {field}
                FROM
                    seen_release
                {'WHERE ' + ' AND '.join(conditions) if conditions else ''};
                """,
                *parameters,
            )

        return [row[field] for row in rows]

    @classmethod
    async def filter(
        cls,
        app: TsundokuApp,
        /,
        title: Optional[str] = None,
        release_group: Optional[str] = None,
        resolution: Optional[str] = None,
        episode: Optional[int] = None,
        version: Optional[str] = None,
    ) -> list[SeenRelease]:
        """
        Gets all SeenReleases from the database,
        filtering by specific criteria.

        Returns
        -------
        list[SeenRelease]
            All SeenReleases.
        """
        parameters = [
            p
            for p in (title, release_group, resolution, episode, version)
            if p is not None
        ]

        conditions = []
        if title is not None:
            conditions.append("title = ?")
        if release_group is not None:
            conditions.append("release_group = ?")
        if resolution is not None:
            conditions.append("resolution = ?")
        if episode is not None:
            conditions.append("episode = ?")
        if version is not None:
            conditions.append("version = ?")

        async with app.acquire_db() as con:
            rows = await con.fetchall(
                f"""
                SELECT
                    title,
                    release_group,
                    episode,
                    resolution,
                    version,
                    torrent_destination,
                    seen_at
                FROM
                    seen_release
                {'WHERE ' + ' AND '.join(conditions) if conditions else ''};
                """,
                *parameters,
            )

        return [SeenRelease(app, *row) for row in rows]

    @staticmethod
    async def delete_old(app: TsundokuApp, /, days: int) -> None:
        """
        Deletes all SeenReleases older than a certain number of days.

        Parameters
        ----------
        days : int
            The number of days.
        """
        logger.info(f"Deleting old SeenReleases... [days={days}]")
        async with app.acquire_db() as con:
            await con.execute(
                """
                    DELETE FROM
                        seen_release as s1
                    WHERE
                        datetime('now', '-' || ? ||' day') > (SELECT
                            MAX(seen_at)
                            FROM seen_release
                            WHERE
                                title = s1.title AND
                                release_group = s1.release_group
                        );
                """,
                days,
            )
            deleted = await con.fetchval("SELECT changes();")

        logger.info(f"Deleted {deleted} old SeenReleases.")

    @classmethod
    async def add(
        cls, app: TsundokuApp, anitopy_result: ParserResult, torrent_destination: str
    ) -> Optional[SeenRelease]:
        """
        Adds a new SeenRelease to the database.

        Parameters
        ----------
        app : TsundokuApp
            The TsundokuApp instance.
        anitopy_result : ParserResult
            The result of parsing a torrent's filename
            with Anitopy.
        torrent_destination : str
            The destination of the torrent.

        Returns
        -------
        SeenRelease
            The SeenRelease that was added.
        """
        if "file_name" not in anitopy_result:
            logger.warning(
                f"Not adding '{anitopy_result}' to seen releases because it has no file name."
            )
            return
        elif "anime_title" not in anitopy_result:
            logger.warning(
                f"Not adding '{anitopy_result['file_name']}' to seen releases because it has no anime title."
            )
            return
        elif "episode_number" not in anitopy_result:
            logger.warning(
                f"Not adding '{anitopy_result['file_name']}' to seen releases because it has no episode number."
            )
            return

        release_group = anitopy_result.get("release_group", "")
        if not release_group:
            logger.warning(
                f"Not adding '{anitopy_result['file_name']}' to seen releases because it has no release group."
            )
            return

        resolution = anitopy_result.get("video_resolution", "")
        if not resolution:
            logger.warning(
                f"Not adding '{anitopy_result['file_name']}' to seen releases because it has no resolution."
            )
            return

        resolution = normalize_resolution(resolution)
        if resolution not in VALID_RESOLUTIONS:
            logger.info(
                f"Not adding '{anitopy_result['file_name']}' to seen releases because it has an invalid resolution '{resolution}'."
            )
            return

        version = anitopy_result.get("release_version", "v0")

        if (
            not isinstance(anitopy_result["episode_number"], str)
            or not anitopy_result["episode_number"].isdigit()
        ):
            logger.warning(
                f"Not adding '{anitopy_result['file_name']}' to seen releases episode number is not an integer."
            )
            return

        episode = int(anitopy_result["episode_number"])

        async with app.acquire_db() as con:
            existing_version = await con.fetchval(
                """
                SELECT
                    version
                FROM
                    seen_release
                WHERE
                    title = ?
                    AND release_group = ?
                    AND episode = ?
                    AND resolution = ?;
                """,
                anitopy_result["anime_title"],
                release_group,
                episode,
                resolution,
            )
            if (
                existing_version
                and compare_version_strings(version, existing_version) <= 0
            ):
                logger.debug(
                    f"Not adding '{anitopy_result['file_name']}' to seen releases because it has a lower (or same) version than the existing release."
                )
                return

            await con.execute(
                """
                INSERT INTO seen_release (
                    title,
                    release_group,
                    episode,
                    resolution,
                    version,
                    torrent_destination
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (title, release_group, episode, resolution)
                DO UPDATE SET
                    version = excluded.version,
                    torrent_destination = excluded.torrent_destination;
                """,
                anitopy_result["anime_title"],
                release_group,
                episode,
                resolution,
                version,
                torrent_destination,
            )

        return cls(
            app,
            anitopy_result["anime_title"],
            release_group,
            episode,
            resolution,
            version,
            torrent_destination,
            datetime.utcnow(),
        )
