from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from sqlite3 import Row
from typing import Any, List, Optional

from tsundoku.webhooks import Webhook


class EntryState(str, Enum):
    """
    Represents the state of an Entry.

    Matches exactly with the Postgres enum.
    """

    downloading = "downloading"
    downloaded = "downloaded"
    renamed = "renamed"
    moved = "moved"
    completed = "completed"


class Entry:
    def __init__(self, app: Any, record: Row) -> None:
        self.id: int = record["id"]
        self.show_id: int = record["show_id"]
        self.episode: int = record["episode"]
        self.state: EntryState = EntryState[record["current_state"]]
        self.torrent_hash: str = record["torrent_hash"]
        self.last_update: datetime = record["last_update"]

        fp = record["file_path"]
        self.file_path: Optional[Path] = Path(fp) if fp is not None else None

        self._app: Any = app
        self._record: Row = record

    def to_dict(self) -> dict:
        """
        Returns the Entry object as a dictionary.

        Returns
        -------
        dict
            The serialized Entry object.
        """
        return {
            "id": self.id,
            "show_id": self.show_id,
            "episode": self.episode,
            "state": self.state.value,
            "torrent_hash": self.torrent_hash,
            "file_path": str(self.file_path),
            "last_update": self.last_update.isoformat(),
        }

    @classmethod
    async def from_show_id(cls, app: Any, show_id: int) -> List[Entry]:
        """
        Retrieves a list of Entries that are associated
        with a specific Show's ID.

        Parameters
        ----------
        app: Any
            The Quart app.
        show_id: int
            The Show's ID.

        Returns
        -------
        List[Entry]
            A list of associated Show Entries.
        """
        async with app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    id,
                    show_id,
                    episode,
                    current_state,
                    torrent_hash,
                    file_path,
                    last_update
                FROM
                    show_entry
                WHERE
                    show_id=?
                ORDER BY
                    episode ASC;
            """,
                show_id,
            )
            entries = await con.fetchall()

        return [Entry(app, entry) for entry in entries]

    async def should_encode(self) -> bool:
        """
        Determines whether or not this entry
        should be post-processed.

        Returns
        -------
        bool
            Whether to post-process or not.
        """
        async with self._app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    post_process
                FROM
                    shows
                WHERE id=?;
            """,
                self.show_id,
            )
            encoding_enabled = await con.fetchval()

        return (
            self.state == "completed"
            and self.file_path is not None
            and encoding_enabled
        )

    async def set_state(self, new_state: EntryState) -> None:
        """
        Updates the database and local object's state.

        Parameters
        ----------
        new_state: EntryState
            The new state to update to.
        """
        self.state = new_state
        async with self._app.acquire_db() as con:
            await con.execute(
                """
                UPDATE show_entry SET
                    current_state = ?,
                    last_update = CURRENT_TIMESTAMP
                WHERE id=?;
            """,
                new_state.value,
                self.id,
            )

        if await self.should_encode():
            self._app.encoder.encode_task(self.id)

        await self._handle_webhooks()

    async def set_path(self, new_path: Path) -> None:
        """
        Updates the database and local object's file path.

        Parameters
        ----------
        new_path: str
            The new path to update to.
        """
        self.file_path = new_path
        async with self._app.acquire_db() as con:
            await con.execute(
                """
                UPDATE show_entry SET
                    file_path = ?
                WHERE id=?;
            """,
                str(new_path),
                self.id,
            )

    async def _handle_webhooks(self) -> None:
        """
        On a state change, if the state is listed as a post event
        for this show, then send this entry to the webhook handling.

        This is an internal method and shouldn't be called unless
        a state change occurs. If called improperly, duplicate
        sends could occur.

        Uses the `self.state` attribute, so call this after
        that is updated.
        """
        webhooks = await Webhook.from_show_id(
            self._app, self.show_id, with_validity=True
        )

        for wh in webhooks:
            triggers = await wh.get_triggers()
            if self.state.value in triggers:
                await wh.send(self.episode, self.state)

    def __repr__(self) -> str:
        return (
            f"<Entry id={self.id} show_id={self.show_id} episode={self.episode}"
            f" state={self.state} hash={self.torrent_hash}>"
        )
