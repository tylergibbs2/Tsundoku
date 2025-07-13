from datetime import datetime
from enum import StrEnum, auto
from pathlib import Path
from sqlite3 import Row
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

from tsundoku.webhooks import Webhook


class EntryState(StrEnum):
    """
    Represents the state of an Entry.

    Matches exactly with the Postgres enum.
    """

    downloading = auto()
    downloaded = auto()
    renamed = auto()
    moved = auto()
    completed = auto()
    failed = auto()


class Entry:
    _app: "TsundokuApp"
    _record: Row

    id: int
    show_id: int
    episode: int
    version: str
    state: EntryState
    torrent_hash: str
    created_manually: bool
    last_update: datetime

    encode: dict | None
    file_path: Path | None

    def __init__(self, app: "TsundokuApp", record: Row) -> None:
        self.id: int = record["id"]
        self.show_id: int = record["show_id"]
        self.episode: int = record["episode"]
        self.version: str = record["version"]
        self.state: EntryState = EntryState[record["current_state"]]
        self.torrent_hash: str = record["torrent_hash"]
        self.created_manually: bool = record["created_manually"]
        self.last_update: datetime = record["last_update"]

        if "queued_at" in dict(record):
            self.encode = {
                "initial_size": record["initial_size"],
                "final_size": record["final_size"],
                "queued_at": record["queued_at"] if record["queued_at"] else None,
                "started_at": record["started_at"] if record["started_at"] else None,
                "ended_at": record["ended_at"] if record["ended_at"] else None,
            }
        else:
            self.encode = None

        fp = record["file_path"]
        self.file_path: Path | None = Path(fp) if fp is not None else None

        self._app: TsundokuApp = app
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
            "version": self.version,
            "state": self.state.value,
            "torrent_hash": self.torrent_hash,
            "file_path": str(self.file_path),
            "created_manually": self.created_manually,
            "last_update": self.last_update,
            "encode": self.encode,
        }

    @classmethod
    async def from_show_id(cls, app: "TsundokuApp", show_id: int) -> list["Entry"]:
        """
        Retrieves a list of Entries that are associated
        with a specific Show's ID.

        Parameters
        ----------
        app: TsundokuApp
            The Quart app.
        show_id: int
            The Show's ID.

        Returns
        -------
        List[Entry]
            A list of associated Show Entries.
        """
        async with app.acquire_db() as con:
            entries = await con.fetchall(
                """
                SELECT
                    se.id,
                    se.show_id,
                    se.episode,
                    se.version,
                    se.current_state,
                    se.torrent_hash,
                    se.file_path,
                    se.created_manually,
                    se.last_update,
                    e.initial_size,
                    e.final_size,
                    e.queued_at,
                    e.started_at,
                    e.ended_at
                FROM
                    show_entry AS se
                LEFT JOIN
                    encode as e
                ON
                    se.id = e.entry_id
                WHERE
                    show_id=?
                ORDER BY
                    episode ASC;
            """,
                show_id,
            )

        return [Entry(app, entry) for entry in entries]

    @classmethod
    async def from_entry_id(cls, app: "TsundokuApp", entry_id: int) -> "Entry":
        """
        Retrieves an Entry by its ID.

        Parameters
        ----------
        app: TsundokuApp
            The Quart app.
        entry_id: int
            The Entry's ID.

        Returns
        -------
        Entry
            The Entry.
        """
        async with app.acquire_db() as con:
            entry = await con.fetchone(
                """
                SELECT
                    se.id,
                    se.show_id,
                    se.episode,
                    se.version,
                    se.current_state,
                    se.torrent_hash,
                    se.file_path,
                    se.created_manually,
                    se.last_update,
                    e.initial_size,
                    e.final_size,
                    e.queued_at,
                    e.started_at,
                    e.ended_at
                FROM
                    show_entry AS se
                LEFT JOIN
                    encode as e
                ON
                    se.id = e.entry_id
                WHERE
                    se.id=?;
            """,
                entry_id,
            )

        return Entry(app, entry)

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
            encoding_enabled = await con.fetchval(
                """
                SELECT
                    post_process
                FROM
                    shows
                WHERE id=?;
            """,
                self.show_id,
            )

        return self.state == "completed" and self.file_path is not None and encoding_enabled

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
            await self._app.encoder.queue(self.id)

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
        webhooks = await Webhook.from_show_id(self._app, self.show_id)

        for wh in webhooks:
            triggers = await wh.get_triggers()
            if self.state.value in triggers:
                await wh.send(self)

    def __repr__(self) -> str:
        return f"<Entry id={self.id} show_id={self.show_id} episode={self.episode} state={self.state} hash={self.torrent_hash}>"
