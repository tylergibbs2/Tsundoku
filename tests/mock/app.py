from __future__ import annotations

import aiofiles
import asyncio
from contextlib import asynccontextmanager, contextmanager
from enum import Enum, auto
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
from uuid import uuid4
from queue import Queue

import aiohttp
from argon2 import PasswordHasher
from fluent.runtime import FluentResourceLoader
from quart import Quart
from quart.typing import TestClientProtocol
from quart_auth import AuthManager
from quart_rate_limiter import RateLimiter

from .dl_client import MockDownloadManager
from tsundoku.app import CustomFluentLocalization
from tsundoku.asqlite import Connection, connect
from tsundoku.blueprints import api_blueprint, ux_blueprint
from tsundoku.flags import Flags
from tsundoku.feeds import Poller, Downloader, Encoder
from tsundoku.user import User


class UserType(Enum):
    REGULAR = auto()
    READONLY = auto()


class QuartConfig:
    SECRET_KEY = "test"
    QUART_AUTH_COOKIE_SECURE = False


class MockTsundokuApp(Quart):
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
        super().__init__("Tsundoku", static_folder=None)

        auth = AuthManager(self)
        RateLimiter(self)

        auth.user_class = User

        self.config.from_object(QuartConfig())

        self.register_blueprint(api_blueprint)
        self.register_blueprint(ux_blueprint)

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
        self.__sync_db_connection.row_factory = sqlite3.Row

        async with self.acquire_db() as con:
            async with aiofiles.open("schema.sql", "r") as fp:
                await con.executescript(await fp.read())

            async with aiofiles.open("tests/mock/_data.sql", "r") as fp:
                await con.executescript(await fp.read())

        await self.poller.update_config()
        await self.downloader.update_config()
        await self.encoder.update_config()

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

    async def test_client(
        self, /, user_type: Optional[UserType] = None
    ) -> TestClientProtocol:
        client = super().test_client(use_cookies=True)
        if user_type is None:
            self.flags.IS_FIRST_LAUNCH = True
            return client
        elif user_type == UserType.REGULAR:
            await self.__create_user(readonly=False)
        elif user_type == UserType.READONLY:
            await self.__create_user(readonly=True)

        await client.post(
            "/login",
            form={"username": "user", "password": "password", "remember": True},
        )

        return client

    def get_fluent(self) -> CustomFluentLocalization:
        if (
            self._active_localization is not None
            and self._active_localization.preferred_locale == self.flags.LOCALE
        ):
            return self._active_localization

        loader = FluentResourceLoader("l10n")
        self._active_localization = CustomFluentLocalization(
            self.flags.LOCALE,
            [self.flags.LOCALE, "en"],
            [f"{self.flags.LOCALE}.ftl", "en.ftl"],
            loader,
        )
        return self._active_localization

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

    async def cleanup(self) -> None:
        await self.__async_db_connection.close()
        self.__sync_db_connection.close()
