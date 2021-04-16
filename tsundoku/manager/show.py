from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from asyncpg import Record
from quart import current_app as app

from tsundoku.webhooks.webhook import Webhook

from .entry import Entry
from .kitsu import KitsuManager


@dataclass
class Show:
    id_: int
    title: str
    desired_format: str
    desired_folder: str
    season: int
    episode_offset: int

    metadata: KitsuManager

    _entries: List[Entry]
    _webhooks: List[Webhook]

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
            "title": self.title,
            "desired_format": self.desired_format,
            "desired_folder": self.desired_folder,
            "season": self.season,
            "episode_offset": self.episode_offset,
            "entries": [e.to_dict() for e in self._entries],
            "metadata": self.metadata.to_dict(),
            "webhooks": [wh.to_dict() for wh in self._webhooks]
        }

    @classmethod
    async def from_data(cls, data: Record) -> Show:
        """
        Creates a Show object from an asyncpg.Record
        of a Show in the database.

        Parameters
        ----------
        data: Record
            The record to create from.

        Returns
        -------
        Show
            The created Show object.
        """
        metadata = await KitsuManager.from_show_id(data["id_"])

        instance = cls(
            **data,
            metadata=metadata,
            _entries=[],
            _webhooks=[]
        )

        await instance.entries()
        await instance.webhooks()

        return instance

    @classmethod
    async def from_id(cls, id_: int) -> Show:
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
        async with app.db_pool.acquire() as con:
            show = await con.fetchrow("""
                SELECT
                    id as id_,
                    title,
                    desired_format,
                    desired_folder,
                    season,
                    episode_offset
                FROM
                    shows
                WHERE id=$1;
            """, id_)

        if not show:
            raise Exception(f"Failed to retrieve show with ID #{id_}")

        metadata = await KitsuManager.from_show_id(show["id_"])

        instance = cls(
            **show,
            metadata=metadata,
            _entries=[],
            _webhooks=[]
        )

        await instance.entries()
        await instance.webhooks()

        return instance

    async def refetch(self) -> None:
        """
        Refetches the Show's metadata and applies
        it to the current instance.
        """
        self.metadata = await KitsuManager.from_show_id(self.id_)

    @staticmethod
    async def insert(**kwargs: Any) -> Show:
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
        async with app.db_pool.acquire() as con:
            new_id = await con.fetchval(
                """
                INSERT INTO
                    shows
                (
                    title,
                    desired_format,
                    desired_folder,
                    season,
                    episode_offset
                )
                VALUES
                    ($1, $2, $3, $4, $5)
                RETURNING
                    id;
            """,
                kwargs["title"],
                kwargs["desired_format"],
                kwargs["desired_folder"],
                kwargs["season"],
                kwargs["episode_offset"]
            )

        return await Show.from_id(new_id)

    async def update(self) -> None:
        """
        Updates a Show in the database using the
        existing object's attributes.
        """
        async with app.db_pool.acquire() as con:
            await con.execute(
                """
                UPDATE
                    shows
                SET
                    title=$1,
                    desired_format=$2,
                    desired_folder=$3,
                    season=$4,
                    episode_offset=$5
                WHERE
                    id=$6
            """,
                self.title,
                self.desired_format,
                self.desired_folder,
                self.season,
                self.episode_offset,
                self.id_
            )

    async def entries(self) -> List[Entry]:
        """
        Retrieves and sets a list of this Show's
        entries.

        Returns
        -------
        List[Entry]
            The Show's entries.
        """
        self._entries = await Entry.from_show_id(app, self.id_)
        return self._entries

    async def webhooks(self) -> List[Webhook]:
        """
        Retrieves and sets a list of this Show's
        webhooks.

        Returns
        -------
        List[Webhook]
            The Show's webhooks.
        """
        self._webhooks = await Webhook.from_show_id(app, self.id_)
        return self._webhooks

    def __repr__(self) -> str:
        return f"<Show id={self.id_} title={self.title}>"
