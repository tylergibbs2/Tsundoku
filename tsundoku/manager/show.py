from dataclasses import dataclass
from datetime import datetime
import logging
from sqlite3 import Row
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

from tsundoku.webhooks.webhook import Webhook

from .entry import Entry
from .kitsu import KitsuManager
from .library import Library

logger = logging.getLogger("tsundoku")


@dataclass
class Show:
    app: TsundokuApp

    id_: int
    library_id: int
    title: str
    title_local: str | None
    desired_format: str | None
    season: int
    episode_offset: int
    watch: bool
    post_process: bool
    preferred_resolution: str | None
    preferred_release_group: str | None
    created_at: datetime

    metadata: KitsuManager

    _entries: list[Entry]
    _webhooks: list[Webhook]

    def to_dict(self) -> dict:
        """
        Serializes a show object.

        Returns
        -------
        dict
            The serialized Show.
        """
        return {
            "id_": self.id_,
            "library_id": self.library_id,
            "title": self.title,
            "title_local": self.title_local,
            "desired_format": self.desired_format,
            "season": self.season,
            "episode_offset": self.episode_offset,
            "watch": self.watch,
            "post_process": self.post_process,
            "preferred_resolution": self.preferred_resolution,
            "preferred_release_group": self.preferred_release_group,
            "created_at": self.created_at,
            "entries": [e.to_dict() for e in self._entries],
            "metadata": self.metadata.to_dict(),
            "webhooks": [wh.to_dict() for wh in self._webhooks],
        }

    @classmethod
    async def from_data(cls, app: TsundokuApp, data: Row) -> "Show":
        """
        Creates a Show object from a sqlite3.Row
        of a Show in the database.

        Parameters
        ----------
        data: Row
            The record to create from.

        Returns
        -------
        Show
            The created Show object.
        """
        data_dict = dict(data)
        metadata_dict = {
            "show_id": data_dict["id_"],
            "kitsu_id": data_dict.pop("kitsu_id", None),
            "slug": data_dict.pop("slug", None),
            "show_status": data_dict.pop("show_status", None),
            "cached_poster_url": data_dict.pop("cached_poster_url", None),
        }
        metadata = await KitsuManager.from_data(app, metadata_dict)

        instance = cls(app, **data_dict, metadata=metadata, _entries=[], _webhooks=[])

        await instance.entries()
        await instance.webhooks()

        return instance

    @classmethod
    async def from_id(cls, app: TsundokuApp, id_: int) -> "Show":
        """
        Retrieves a Show from the database based on
        a passed identifier.

        Parameters
        ----------
        id_: int
            The Show ID to retrieve.

        Returns
        -------
        Show
            The retrieved Show's object.
        """
        async with app.acquire_db() as con:
            show = await con.fetchone(
                """
                SELECT
                    id as id_,
                    library_id,
                    title,
                    title_local,
                    desired_format,
                    season,
                    episode_offset,
                    watch,
                    post_process,
                    preferred_resolution,
                    preferred_release_group,
                    created_at
                FROM
                    shows
                WHERE id=?;
            """,
                id_,
            )

        if not show:
            logger.error(f"Failed to retrieve show with ID #{id_}")
            raise ValueError(f"Failed to retrieve show with ID #{id_}")

        metadata = await KitsuManager.from_show_id(app, show["id_"])

        instance = cls(app, **show, metadata=metadata, _entries=[], _webhooks=[])  # type: ignore

        await instance.entries()
        await instance.webhooks()

        return instance

    async def refetch(self) -> None:
        """
        Refetches the Show's metadata and applies
        it to the current instance.
        """
        self.metadata = await KitsuManager.from_show_id(self.app, self.id_)

    async def get_library(self) -> Library:
        """
        Retrieves the Library for the show.
        """
        if self.library_id is None:
            raise ValueError(f"Show '{self.id_}' has no library")

        return await Library.from_id(self.app, self.library_id)

    @staticmethod
    async def insert(
        app: TsundokuApp,
        /,
        library_id: int,
        title: str,
        title_local: str | None,
        desired_format: str | None,
        season: int,
        episode_offset: int,
        watch: bool,
        post_process: bool,
        preferred_resolution: str | None,
        preferred_release_group: str | None,
    ) -> "Show":
        """
        Inserts a Show into the database based on the
        passed keyword arguments.

        Parameters
        ----------
        **kwargs: Any
            List of arguments to use when
            creating the Show object.

        Returns
        -------
        Show
            The inserted Show object.
        """
        async with app.acquire_db() as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO
                        shows
                    (
                        library_id,
                        title,
                        title_local,
                        desired_format,
                        season,
                        episode_offset,
                        watch,
                        post_process,
                        preferred_resolution,
                        preferred_release_group
                    )
                    VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                    library_id,
                    title,
                    title_local,
                    desired_format,
                    season,
                    episode_offset,
                    watch,
                    post_process,
                    preferred_resolution,
                    preferred_release_group,
                )
                new_id = cur.lastrowid

        if new_id is None:
            raise Exception("Failed to insert show into database")

        return await Show.from_id(app, new_id)

    async def update(self) -> None:
        """
        Updates a Show in the database using the
        existing object's attributes.
        """
        async with self.app.acquire_db() as con:
            await con.execute(
                """
                UPDATE
                    shows
                SET
                    library_id=?,
                    title=?,
                    title_local=?,
                    desired_format=?,
                    season=?,
                    episode_offset=?,
                    watch=?,
                    post_process=?,
                    preferred_resolution=?,
                    preferred_release_group=?
                WHERE
                    id=?
            """,
                self.library_id,
                self.title,
                self.title_local,
                self.desired_format,
                self.season,
                self.episode_offset,
                self.watch,
                self.post_process,
                self.preferred_resolution,
                self.preferred_release_group,
                self.id_,
            )

    async def entries(self) -> list[Entry]:
        """
        Retrieves and sets a list of this Show's
        entries.

        Returns
        -------
        List[Entry]
            The Show's entries.
        """
        self._entries = await Entry.from_show_id(self.app, self.id_)
        return self._entries

    async def webhooks(self) -> list[Webhook]:
        """
        Retrieves and sets a list of this Show's
        webhooks.

        Returns
        -------
        List[Webhook]
            The Show's webhooks.
        """
        self._webhooks = await Webhook.from_show_id(self.app, self.id_)
        return self._webhooks

    def __repr__(self) -> str:
        return f"<Show id={self.id_} title={self.title}>"
