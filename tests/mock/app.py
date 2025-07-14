import asyncio
from collections.abc import AsyncIterator, Iterator, MutableSet
from contextlib import AbstractAsyncContextManager, AbstractContextManager, asynccontextmanager, contextmanager
from enum import Enum, auto
from queue import Queue
import sqlite3
from typing import ClassVar
from uuid import uuid4

import aiofiles
import aiohttp
from argon2 import PasswordHasher
from fluent.runtime import FluentResourceLoader
from quart import Quart
from quart.typing import TestClientProtocol
from quart_auth import AuthManager
from quart_rate_limiter import RateLimiter

from tsundoku.app import CustomFluentLocalization
from tsundoku.asqlite import Connection, connect
from tsundoku.blueprints import api_blueprint, ux_blueprint
from tsundoku.feeds import Downloader, Poller
from tsundoku.flags import Flags
from tsundoku.user import User

from .dl_client import MockDownloadManager


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

    flags: Flags

    cached_bundle_hash: str | None = None
    _active_localization: CustomFluentLocalization | None = None
    _tasks: ClassVar[list[asyncio.Task]] = []

    __async_db_connection: Connection
    __sync_db_connection: sqlite3.Connection

    def __init__(self) -> None:
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

    async def setup(self) -> None:
        self.__async_db_connection = await connect("file:tsundoku?mode=memory&cache=shared", uri=True)
        self.__sync_db_connection = sqlite3.connect("file:tsundoku?mode=memory&cache=shared", uri=True)
        self.__sync_db_connection.row_factory = sqlite3.Row

        async with self.acquire_db() as con:
            async with aiofiles.open("schema.sql") as fp:
                await con.executescript(await fp.read())

            async with aiofiles.open("tests/mock/_data.sql") as fp:
                await con.executescript(await fp.read())

        await self.poller.update_config()
        await self.downloader.update_config()

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

    async def test_client(self, /, user_type: UserType | None = None) -> TestClientProtocol:
        client = super().test_client(use_cookies=True)
        if user_type is None:
            self.flags.IS_FIRST_LAUNCH = True
            return client
        if user_type == UserType.REGULAR:
            await self.__create_user(readonly=False)
        elif user_type == UserType.READONLY:
            await self.__create_user(readonly=True)

        await client.post(
            "/login",
            form={"username": "user", "password": "password", "remember": True},
        )

        return client

    def get_fluent(self) -> CustomFluentLocalization:
        if self._active_localization is not None and self._active_localization.preferred_locale == self.flags.LOCALE:
            return self._active_localization

        loader = FluentResourceLoader("l10n")
        self._active_localization = CustomFluentLocalization(
            self.flags.LOCALE,
            [self.flags.LOCALE, "en"],
            [f"{self.flags.LOCALE}.ftl", "en.ftl"],
            loader,
        )
        return self._active_localization

    def acquire_db(self) -> AbstractAsyncContextManager[Connection]:
        @asynccontextmanager
        async def async_con_generator() -> AsyncIterator[Connection]:  # noqa: RUF029
            yield self.__async_db_connection

        return async_con_generator()

    def sync_acquire_db(self) -> AbstractContextManager[sqlite3.Connection]:
        @contextmanager
        def sync_con_generator() -> Iterator[sqlite3.Connection]:
            yield self.__sync_db_connection

        return sync_con_generator()

    async def cleanup(self) -> None:
        await self.__async_db_connection.close()
        self.__sync_db_connection.close()
