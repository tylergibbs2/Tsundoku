from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

from tsundoku.constants import VALID_RESOLUTIONS
from tsundoku.utils import ParserResult, compare_version_strings, normalize_resolution

logger = logging.getLogger("tsundoku")


@dataclass
class SeenRelease:
    app: "TsundokuApp"

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
        app: "TsundokuApp",
        field: str,
        /,
        title: str | None = None,
        release_group: str | None = None,
        resolution: str | None = None,
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
                {"WHERE " + " AND ".join(conditions) if conditions else ""};
                """,
                *parameters,
            )

        return [row[field] for row in rows]

    @classmethod
    async def filter(
        cls,
        app: "TsundokuApp",
        /,
        title: str | None = None,
        release_group: str | None = None,
        resolution: str | None = None,
        episode: int | None = None,
        version: str | None = None,
    ) -> list["SeenRelease"]:
        """
        Gets all SeenReleases from the database,
        filtering by specific criteria.

        Returns
        -------
        list[SeenRelease]
            All SeenReleases.
        """
        parameters = [p for p in (title, release_group, resolution, episode, version) if p is not None]

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
                {"WHERE " + " AND ".join(conditions) if conditions else ""};
                """,
                *parameters,
            )

        return [SeenRelease(app, *row) for row in rows]

    @staticmethod
    async def delete_old(app: "TsundokuApp", /, days: int) -> None:
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
    async def add(cls, app: "TsundokuApp", parsed: ParserResult, torrent_destination: str) -> "SeenRelease | None":
        """
        Adds a new SeenRelease to the database.

        Parameters
        ----------
        app : TsundokuApp
            The TsundokuApp instance.
        parsed : ParserResult
            The result of parsing a torrent's filename
            with anitomy.
        torrent_destination : str
            The destination of the torrent.

        Returns
        -------
        SeenRelease
            The SeenRelease that was added.
        """
        if "file_name" not in parsed:
            logger.warning(f"Not adding '{parsed}' to seen releases because it has no file name.")
            return None
        if "anime_title" not in parsed:
            logger.warning(f"Not adding '{parsed['file_name']}' to seen releases because it has no anime title.")
            return None
        if "episode_number" not in parsed:
            logger.warning(f"Not adding '{parsed['file_name']}' to seen releases because it has no episode number.")
            return None

        release_group = parsed.get("release_group", "")
        if not release_group:
            logger.warning(f"Not adding '{parsed['file_name']}' to seen releases because it has no release group.")
            return None

        resolution = parsed.get("video_resolution", "")
        if not resolution:
            logger.warning(f"Not adding '{parsed['file_name']}' to seen releases because it has no resolution.")
            return None

        resolution = normalize_resolution(resolution)
        if resolution not in VALID_RESOLUTIONS:
            logger.info(f"Not adding '{parsed['file_name']}' to seen releases because it has an invalid resolution '{resolution}'.")
            return None

        version = parsed.get("release_version", "v0")

        if not isinstance(parsed["episode_number"], str) or not parsed["episode_number"].isdigit():
            logger.warning(f"Not adding '{parsed['file_name']}' to seen releases episode number is not an integer.")
            return None

        episode = int(parsed["episode_number"])

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
                parsed["anime_title"],
                release_group,
                episode,
                resolution,
            )
            if existing_version and compare_version_strings(version, existing_version) <= 0:
                logger.debug(f"Not adding '{parsed['file_name']}' to seen releases because it has a lower (or same) version than the existing release.")
                return None

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
                parsed["anime_title"],
                release_group,
                episode,
                resolution,
                version,
                torrent_destination,
            )

        return cls(
            app,
            parsed["anime_title"],
            release_group,
            episode,
            resolution,
            version,
            torrent_destination,
            datetime.now(UTC).replace(tzinfo=None),
        )
