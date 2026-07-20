from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import AbstractAsyncContextManager, AbstractContextManager, asynccontextmanager, contextmanager
from enum import Enum, auto
import sqlite3
from uuid import uuid4

import aiofiles
from argon2 import PasswordHasher
from fastapi import FastAPI
import httpx

from tsundoku.app import TsundokuAppState, create_app
from tsundoku.asqlite import Connection, connect
from tsundoku.feeds import Downloader, Poller
from tsundoku.ratelimit import limiter

from .dl_client import MockDownloadManager


class UserType(Enum):
    REGULAR = auto()
    READONLY = auto()


@asynccontextmanager
async def _noop_lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


class MockTsundokuAppState(TsundokuAppState):
    """An in-memory, test-oriented variant of :class:`TsundokuAppState`.

    The application lifespan is stubbed out; the database lives in a shared
    in-memory SQLite instance, and the download manager is mocked.
    """

    dl_client: MockDownloadManager

    def __init__(self) -> None:
        super().__init__()
        self.dl_client = MockDownloadManager()

        # The rate limiter uses global in-memory state that would otherwise
        # bleed across tests; disable it for the test app.
        limiter.enabled = False

        self.asgi_app = create_app(self, lifespan_handler=_noop_lifespan)

    async def setup(self) -> None:
        self._async_db = await connect("file:tsundoku?mode=memory&cache=shared", uri=True)
        self._sync_db = sqlite3.connect("file:tsundoku?mode=memory&cache=shared", uri=True)
        self._sync_db.row_factory = sqlite3.Row

        async with self.acquire_db() as con:
            async with aiofiles.open("schema.sql") as fp:
                await con.executescript(await fp.read())

            async with aiofiles.open("tests/mock/_data.sql") as fp:
                await con.executescript(await fp.read())

        self.poller = Poller(self)
        self.downloader = Downloader(self)

        await self.poller.update_config()
        await self.downloader.update_config()

    def acquire_db(self) -> AbstractAsyncContextManager[Connection]:
        @asynccontextmanager
        async def _gen() -> AsyncIterator[Connection]:
            yield self._async_db

        return _gen()

    def sync_acquire_db(self) -> AbstractContextManager[sqlite3.Connection]:
        @contextmanager
        def _gen() -> Iterator[sqlite3.Connection]:
            yield self._sync_db

        return _gen()

    async def __create_user(self, /, readonly: bool = False) -> None:
        pw_hash = PasswordHasher().hash("password")
        async with self.acquire_db() as con:
            await con.execute(
                """
                INSERT INTO
                    users
                    (username, password_hash, api_key, readonly)
                VALUES
                    (?, ?, ?, ?);
            """,
                "user",
                pw_hash,
                str(uuid4()),
                readonly,
            )

    async def test_client(self, /, user_type: UserType | None = None) -> httpx.AsyncClient:
        transport = httpx.ASGITransport(app=self.asgi_app)
        client = httpx.AsyncClient(transport=transport, base_url="http://testserver", follow_redirects=False)

        if user_type is None:
            self.flags.IS_FIRST_LAUNCH = True
            return client

        if user_type == UserType.REGULAR:
            await self.__create_user(readonly=False)
        elif user_type == UserType.READONLY:
            await self.__create_user(readonly=True)

        await client.post(
            "/login",
            data={"username": "user", "password": "password", "remember": "true"},
        )

        return client

    async def cleanup(self) -> None:
        await self._async_db.close()
        self._sync_db.close()
