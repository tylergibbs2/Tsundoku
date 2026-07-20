from datetime import datetime
import logging
from sqlite3 import Row
from typing import TYPE_CHECKING, Self

from pydantic import Field

from tsundoku.model import DBModel
from tsundoku.webhooks.webhook import Webhook

from .entry import Entry
from .kitsu import KitsuManager
from .library import Library

if TYPE_CHECKING:
    from tsundoku.app import TsundokuAppState

logger = logging.getLogger("tsundoku")


class Show(DBModel):
    id_: int
    library_id: int
    title: str
    title_local: str | None
    desired_format: str | None
    season: int
    episode_offset: int
    watch: bool
    preferred_resolution: str | None
    preferred_release_group: str | None
    created_at: datetime

    metadata: KitsuManager | None = None

    entries: list[Entry] = Field(default_factory=list)
    webhooks: list[Webhook] = Field(default_factory=list)

    @property
    def internal_title(self) -> str:
        return self.title_local if self.title_local else self.title

    @classmethod
    async def from_data(cls, app: "TsundokuAppState", data: Row) -> Self:
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
        data_dict.pop("last_update", None)

        metadata_dict = {
            "show_id": data_dict["id_"],
            "kitsu_id": data_dict.pop("kitsu_id", None),
            "slug": data_dict.pop("slug", None),
            "show_status": data_dict.pop("show_status", None),
            "cached_poster_url": data_dict.pop("cached_poster_url", None),
        }
        metadata = await KitsuManager.from_data(app, metadata_dict)

        instance = cls(**data_dict, metadata=metadata)._bind(app)

        await instance.load_entries()
        await instance.load_webhooks()

        return instance

    @classmethod
    async def from_id(cls, app: "TsundokuAppState", id_: int, lazy_metadata: bool = False, lazy_entries: bool = False, lazy_webhooks: bool = False) -> Self:
        """
        Retrieves a Show from the database based on
        a passed identifier.

        Parameters
        ----------
        id_: int
            The Show ID to retrieve.
        lazy_metadata: bool
            If True, do not fetch metadata immediately.
        lazy_entries: bool
            If True, do not fetch entries immediately.
        lazy_webhooks: bool
            If True, do not fetch webhooks immediately.

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

        if lazy_metadata:
            metadata = None
        else:
            metadata = await KitsuManager.from_show_id(app, show["id_"])

        instance = cls(**show, metadata=metadata)._bind(app)

        if not lazy_entries:
            await instance.load_entries()
        if not lazy_webhooks:
            await instance.load_webhooks()

        return instance

    async def ensure_metadata(self) -> None:
        """
        Ensures that metadata is loaded, fetching it if necessary.
        """
        if self.metadata is None:
            self.metadata = await KitsuManager.from_show_id(self.app, self.id_)

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
        app: "TsundokuAppState",
        /,
        library_id: int,
        title: str,
        title_local: str | None,
        desired_format: str | None,
        season: int,
        episode_offset: int,
        watch: bool,
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
        async with app.acquire_db() as con, con.cursor() as cur:
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
                        preferred_resolution,
                        preferred_release_group
                    )
                    VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                library_id,
                title,
                title_local,
                desired_format,
                season,
                episode_offset,
                watch,
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
                self.preferred_resolution,
                self.preferred_release_group,
                self.id_,
            )

    async def load_entries(self) -> list[Entry]:
        """
        Retrieves and sets a list of this Show's
        entries.

        Returns
        -------
        List[Entry]
            The Show's entries.
        """
        self.entries = await Entry.from_show_id(self.app, self.id_)
        return self.entries

    async def load_webhooks(self) -> list[Webhook]:
        """
        Retrieves and sets a list of this Show's
        webhooks.

        Returns
        -------
        List[Webhook]
            The Show's webhooks.
        """
        self.webhooks = await Webhook.from_show_id(self.app, self.id_)
        return self.webhooks

    def __repr__(self) -> str:
        return f"<Show id={self.id_} title={self.title}>"
