from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from sqlite3 import Row
from typing import Any, List

from quart import current_app as app

from tsundoku.webhooks.webhook import Webhook

from .entry import Entry
from .kitsu import KitsuManager

logger = logging.getLogger("tsundoku")


@dataclass
class Show:
    id_: int
    title: str
    desired_format: str
    desired_folder: str
    season: int
    episode_offset: int
    watch: bool
    created_at: datetime

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
            "watch": self.watch,
            "created_at": self.created_at.isoformat(),
            "entries": [e.to_dict() for e in self._entries],
            "metadata": self.metadata.to_dict(),
            "webhooks": [wh.to_dict() for wh in self._webhooks]
        }

    @classmethod
    async def from_data(cls, data: Row) -> Show:
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
        metadata = await KitsuManager.from_show_id(data["id_"])

        instance = cls(
            **dict(data),
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
        async with app.acquire_db() as con:
            await con.execute("""
                SELECT
                    id as id_,
                    title,
                    desired_format,
                    desired_folder,
                    season,
                    episode_offset,
                    watch,
                    created_at
                FROM
                    shows
                WHERE id=?;
            """, id_)
            show = await con.fetchone()

        if not show:
            logger.error(f"Failed to retrieve show with ID #{id_}")
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
        async with app.acquire_db() as con:
            await con.execute(
                """
                INSERT INTO
                    shows
                (
                    title,
                    desired_format,
                    desired_folder,
                    season,
                    episode_offset,
                    watch
                )
                VALUES
                    (?, ?, ?, ?, ?, ?);
            """,
                kwargs["title"],
                kwargs["desired_format"],
                kwargs["desired_folder"],
                kwargs["season"],
                kwargs["episode_offset"],
                kwargs["watch"]
            )
            new_id = con.lastrowid

        return await Show.from_id(new_id)

    async def update(self) -> None:
        """
        Updates a Show in the database using the
        existing object's attributes.
        """
        async with app.acquire_db() as con:
            await con.execute(
                """
                UPDATE
                    shows
                SET
                    title=?,
                    desired_format=?,
                    desired_folder=?,
                    season=?,
                    episode_offset=?,
                    watch=?
                WHERE
                    id=?
            """,
                self.title,
                self.desired_format,
                self.desired_folder,
                self.season,
                self.episode_offset,
                self.watch,
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
