from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, AbstractContextManager, asynccontextmanager
import logging
import os
from pathlib import Path
import secrets
import sqlite3
from uuid import uuid4

import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from argon2 import PasswordHasher
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fluent.runtime import FluentResourceLoader
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware
from starlette.types import Lifespan

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import tsundoku.asqlite
from tsundoku.asqlite import Connection
from tsundoku.auth import NotAuthenticatedError
from tsundoku.blueprints import api_router, ux_router
from tsundoku.config import GeneralConfig
from tsundoku.constants import DATA_DIR, DATABASE_FILE_NAME
from tsundoku.database import acquire, migrate, sync_acquire
from tsundoku.dl_client import Manager
from tsundoku.feeds import Downloader, Poller
from tsundoku.flags import Flags
from tsundoku.fluent import CustomFluentLocalization
from tsundoku.git import check_for_updates
from tsundoku.log import setup_logging
from tsundoku.ratelimit import limiter
from tsundoku.responses import APIError, ErrorEnvelope
from tsundoku.templating import STATIC_URL_PATH, flash

__all__ = ["CustomFluentLocalization", "TsundokuAppState", "create_app", "insert_user", "run"]

logger = logging.getLogger("tsundoku")

_STATIC_DIR = Path(__file__).parent / "blueprints" / "ux" / "static"


def _resolve_secret_key(flags: Flags) -> str:
    env = os.getenv("SECRET_KEY")
    if env:
        return env
    return "debug" if flags.IS_DEBUG else secrets.token_urlsafe(16)


class TsundokuAppState:
    """Shared application state and lifecycle for Tsundoku.

    This is a plain container (not the ASGI app) holding everything the
    domain layer needs: database accessors, the download-client manager,
    the poller/downloader background tasks, feature flags, and the aiohttp
    session. It is stored on ``app.state.ctx`` and injected into request
    handlers via the ``StateDep`` dependency.
    """

    session: aiohttp.ClientSession
    dl_client: Manager
    poller: Poller
    downloader: Downloader

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()

        self.connected_websockets: set[asyncio.Queue[str]] = set()
        self.source_lock = asyncio.Lock()
        self.flags = Flags()
        self.secret_key = _resolve_secret_key(self.flags)

        self.cached_bundle_hash: str | None = None
        self._active_localization: CustomFluentLocalization | None = None
        self._tasks: list[asyncio.Task[None]] = []

    def acquire_db(self) -> AbstractAsyncContextManager[Connection]:
        return acquire()

    def sync_acquire_db(self) -> AbstractContextManager[sqlite3.Connection]:
        return sync_acquire()

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

    async def startup(self) -> None:
        await self._setup_db()
        await self._setup_session()
        await self._setup_tasks()

    async def _setup_db(self) -> None:
        async with self.acquire_db() as con:
            logger.debug("VACUUMing database...")
            await con.execute("VACUUM;")
            logger.debug("Database VACUUM'd.")

            users = await con.fetchval("SELECT COUNT(*) FROM users;")
            locale = await con.fetchval("SELECT locale FROM general_config;")

        self.flags.LOCALE = locale or "en"

        if not users:
            logger.warning("No existing users! Opening the app will result in a one-time registration page. Alternatively, you can create a user with the `tsundoku --create-user` command.")
            self.flags.IS_FIRST_LAUNCH = True

    async def _setup_session(self) -> None:
        jar = aiohttp.CookieJar(unsafe=True)  # unsafe has to be True to store cookies from non-DNS URLs, i.e local IPs.

        logger.debug("Creating aiohttp ClientSession...")
        self.session = aiohttp.ClientSession(cookie_jar=jar, timeout=aiohttp.ClientTimeout(total=15.0))
        logger.debug("Creating interface to downloader client...")
        self.dl_client = Manager(self, self.session)

        res = await self.dl_client.test_client()
        self.flags.DL_CLIENT_CONNECTION_ERROR = not res.success

    async def _setup_tasks(self) -> None:
        logger.debug("Starting APScheduler...")
        self.scheduler.start()
        self.scheduler.add_job(check_for_updates, CronTrigger.from_crontab("* 4 * * *"), args=[self])

        async def poller() -> None:
            self.poller = Poller(self)
            await self.poller.start()

        async def downloader() -> None:
            self.downloader = Downloader(self)
            await self.downloader.start()

        logger.debug("Starting task: Poller")
        self._tasks.append(asyncio.create_task(poller(), name="Poller"))
        logger.debug("Starting task: Downloader")
        self._tasks.append(asyncio.create_task(downloader(), name="Downloader"))

        logger.debug("All tasks created.")

    async def shutdown(self) -> None:
        logger.debug("Cleanup: Attempting to cancel tasks...")
        self.scheduler.shutdown()

        for task in self._tasks:
            logger.debug(f"Cleanup: Attempting to cancel task '{task.get_name()}'...")
            task.cancel()

        logger.debug("Cleanup: Closing aiohttp session...")
        try:
            await self.session.close()
        except Exception:
            logger.warning("Cleanup: Could not close aiohttp session!", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    state: TsundokuAppState = app.state.ctx
    await state.startup()
    try:
        yield
    finally:
        await state.shutdown()


async def _api_error_handler(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, APIError)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorEnvelope(status=exc.status_code, error=exc.message).model_dump(),
    )


async def _not_authenticated_handler(request: Request, exc: Exception) -> Response:
    state: TsundokuAppState = request.app.state.ctx
    target = "/register" if state.flags.IS_FIRST_LAUNCH else "/login"
    return RedirectResponse(target, status_code=302)


async def _validation_error_handler(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, RequestValidationError)
    errors = exc.errors()
    message = errors[0]["msg"] if errors else "Invalid request."
    return JSONResponse(
        status_code=422,
        content=ErrorEnvelope(status=422, error=message).model_dump(),
    )


async def _rate_limit_handler(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, RateLimitExceeded)
    flash(request, "Too many requests. Please try again shortly.", "error")
    return RedirectResponse(str(request.url), status_code=302)


def create_app(state: TsundokuAppState | None = None, *, lifespan_handler: Lifespan[FastAPI] = lifespan) -> FastAPI:
    if state is None:
        state = TsundokuAppState()

    app = FastAPI(title="Tsundoku", lifespan=lifespan_handler)
    app.state.ctx = state
    app.state.limiter = limiter

    app.add_middleware(SessionMiddleware, secret_key=state.secret_key, https_only=False)

    app.add_exception_handler(APIError, _api_error_handler)
    app.add_exception_handler(NotAuthenticatedError, _not_authenticated_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

    app.include_router(api_router)
    app.include_router(ux_router)

    app.mount(STATIC_URL_PATH, StaticFiles(directory=str(_STATIC_DIR)), name="static")

    return app


async def insert_user(username: str, password: str) -> None:
    database_source = DATA_DIR / DATABASE_FILE_NAME
    await migrate(database_source)

    pw_hash = PasswordHasher().hash(password)
    async with tsundoku.asqlite.connect(f"{DATA_DIR / DATABASE_FILE_NAME}") as con:
        await con.execute(
            """
            INSERT INTO
                users
                (username, password_hash, api_key)
            VALUES
                (?, ?, ?);
        """,
            username,
            pw_hash,
            str(uuid4()),
        )


def get_bind(state: TsundokuAppState) -> tuple[str, int]:
    """Return the host and port bindings to run the app on."""
    cfg = GeneralConfig.sync_retrieve(state, ensure_exists=True)

    host = os.getenv("HOST") or cfg.host
    port_value: str | int = os.getenv("PORT") or cfg.port

    if isinstance(port_value, str) and not port_value.isdigit():
        raise ValueError("Port must be a number!")

    port = int(port_value)
    if not 0 < port < 65536:
        raise ValueError("Port must be between [1, 65536)!")

    return host, port


async def run() -> None:
    import uvicorn

    database_source = DATA_DIR / DATABASE_FILE_NAME
    await migrate(database_source)

    app = create_app()
    setup_logging(app.state.ctx)

    host, port = get_bind(app.state.ctx)
    logger.debug(f"Attempting to bind to {host}:{port}")

    config = uvicorn.Config(app, host=host, port=port, log_config=None)
    server = uvicorn.Server(config)
    await server.serve()
