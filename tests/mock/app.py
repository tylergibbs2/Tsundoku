from __future__ import annotations

import aiofiles
import asyncio
from contextlib import asynccontextmanager, contextmanager
import sqlite3
from typing import (
    AsyncIterator,
    AsyncContextManager,
    ContextManager,
    Iterator,
    List,
    MutableSet,
    Optional,
)
from queue import Queue
from weakref import ref, ReferenceType

import aiohttp

from .dl_client import MockDownloadManager
from tsundoku.app import CustomFluentLocalization
from tsundoku.asqlite import Connection, connect
from tsundoku.dl_client import Manager
from tsundoku.flags import Flags
from tsundoku.feeds import Poller, Downloader, Encoder


class MockTsundokuAppContext:
    _app: ReferenceType[MockTsundokuApp]

    def __init__(self, app: ReferenceType[MockTsundokuApp]):
        self._app = app

    @property
    def app(self) -> MockTsundokuApp:
        app = self._app()
        if app is None:
            raise Exception("mock app became none")

        return app


class MockTsundokuApp:
    session: aiohttp.ClientSession
    dl_client: MockDownloadManager

    connected_websockets: MutableSet[Queue[str]]

    source_lock: asyncio.Lock

    poller: Poller
    downloader: Downloader
    encoder: Encoder

    flags: Flags

    cached_bundle_hash: Optional[str] = None
    _active_localization: Optional[CustomFluentLocalization] = None
    _tasks: List[asyncio.Task] = []

    __async_db_connection: Connection
    __sync_db_connection: sqlite3.Connection

    def __init__(self):
        self.connected_websockets = set()

        self.source_lock = asyncio.Lock()

        self.flags = Flags()

        self.dl_client = MockDownloadManager()

        self.poller = Poller(self.app_context())
        self.downloader = Downloader(self.app_context())
        self.encoder = Encoder(self.app_context())

    async def setup(self) -> None:
        self.__async_db_connection = await connect(
            "file::memory:?cache=shared", uri=True
        )
        self.__sync_db_connection = sqlite3.connect(
            "file::memory:?cache=shared", uri=True
        )

        async with self.acquire_db() as con:
            async with aiofiles.open("schema.sql", "r") as fp:
                await con.executescript(await fp.read())

            async with aiofiles.open("tests/mock/_data.sql", "r") as fp:
                await con.executescript(await fp.read())

        await self.poller.update_config()
        await self.downloader.update_config()
        await self.encoder.update_config()

    def app_context(self) -> MockTsundokuAppContext:
        return MockTsundokuAppContext(ref(self))

    def acquire_db(self) -> AsyncContextManager[Connection]:
        @asynccontextmanager
        async def async_con_generator() -> AsyncIterator[Connection]:
            yield self.__async_db_connection

        return async_con_generator()

    def sync_acquire_db(self) -> ContextManager[sqlite3.Connection]:
        @contextmanager
        def sync_con_generator() -> Iterator[sqlite3.Connection]:
            yield self.__sync_db_connection

        return sync_con_generator()

    def add_url_rule(self, *_, **__):
        ...

    async def cleanup(self) -> None:
        await self.__async_db_connection.close()
        self.__sync_db_connection.close()
