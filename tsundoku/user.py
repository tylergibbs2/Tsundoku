from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuAppState


@dataclass(slots=True)
class User:
    """A resolved, authenticated user.

    Instances are always fully resolved against the database via
    :meth:`from_id` or :meth:`from_api_key`; there is no lazy-loading
    state to manage.
    """

    id: int
    username: str
    api_key: str
    readonly: bool

    @classmethod
    async def from_id(cls, state: TsundokuAppState, user_id: int) -> User | None:
        """Resolve a :class:`User` from its database identifier.

        Returns ``None`` if no user with that identifier exists.
        """
        async with state.acquire_db() as con:
            record = await con.fetchone(
                """
                SELECT
                    id,
                    username,
                    api_key,
                    readonly
                FROM
                    users
                WHERE id = ?;
                """,
                user_id,
            )

        if record is None:
            return None

        return cls(
            id=record["id"],
            username=record["username"],
            api_key=record["api_key"],
            readonly=bool(record["readonly"]),
        )

    @classmethod
    async def from_api_key(cls, state: TsundokuAppState, api_key: str) -> User | None:
        """Resolve a :class:`User` from a bearer API key."""
        async with state.acquire_db() as con:
            record = await con.fetchone(
                """
                SELECT
                    id,
                    username,
                    api_key,
                    readonly
                FROM
                    users
                WHERE api_key = ?;
                """,
                api_key,
            )

        if record is None:
            return None

        return cls(
            id=record["id"],
            username=record["username"],
            api_key=record["api_key"],
            readonly=bool(record["readonly"]),
        )
