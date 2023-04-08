from __future__ import annotations

import asyncio
from asyncio.queues import Queue
import logging
import os
from pathlib import Path
import secrets
import sqlite3
from typing import (
    Optional,
    Tuple,
    MutableSet,
    List,
    Callable,
    AsyncContextManager,
    ContextManager,
)
from uuid import uuid4

import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from argon2 import PasswordHasher
from fluent.runtime import FluentResourceLoader
from quart import Quart
from quart_auth import AuthManager
from quart_rate_limiter import RateLimiter

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import tsundoku.asqlite
from tsundoku.asqlite import Connection
from tsundoku.blueprints.api import api_blueprint
from tsundoku.blueprints.ux import ux_blueprint
from tsundoku.config import GeneralConfig
from tsundoku.constants import DATA_DIR, DATABASE_FILE_NAME
from tsundoku.database import acquire, migrate, sync_acquire
from tsundoku.dl_client import Manager
from tsundoku.feeds import Downloader, Encoder, Poller
from tsundoku.flags import Flags
from tsundoku.fluent import CustomFluentLocalization
from tsundoku.git import check_for_updates
from tsundoku.log import setup_logging
from tsundoku.user import User


class TsundokuApp(Quart):
    session: aiohttp.ClientSession
    scheduler: AsyncIOScheduler

    connected_websockets: MutableSet[Queue[str]]
    source_lock: asyncio.Lock

    dl_client: Manager
    poller: Poller
    downloader: Downloader
    encoder: Encoder

    acquire_db: Callable[..., AsyncContextManager[Connection]]
    sync_acquire_db: Callable[..., ContextManager[sqlite3.Connection]]

    flags: Flags

    cached_bundle_hash: Optional[str] = None
    _active_localization: Optional[CustomFluentLocalization] = None
    _tasks: List[asyncio.Task] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scheduler = AsyncIOScheduler()

        self.acquire_db = acquire
        self.sync_acquire_db = sync_acquire

        self.connected_websockets = set()
        self.flags = Flags()

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


app: TsundokuApp = TsundokuApp("Tsundoku", static_folder=None)

auth = AuthManager(app)
rate_limiter = RateLimiter(app)

auth.user_class = User

logger = logging.getLogger("tsundoku")


if os.getenv("SECRET_KEY"):
    secret_key = os.getenv("SECRET_KEY")
else:
    secret_key = secrets.token_urlsafe(16) if not app.flags.IS_DEBUG else "debug"


class QuartConfig:
    SECRET_KEY = secret_key
    QUART_AUTH_COOKIE_SECURE = False


app.config.from_object(QuartConfig())


async def insert_user(username: str, password: str) -> None:
    await migrate()

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


@app.url_defaults
def add_hash_for_webpack_bundle(endpoint: str, values: dict) -> None:
    filename = values.get("filename")
    if endpoint != "ux.static" or filename != "js/root.js":
        return

    if app.cached_bundle_hash is not None and not app.flags.IS_DEBUG:
        values["filename"] = f"js/root.{app.cached_bundle_hash}.js"
        return

    js_folder = Path("tsundoku", "blueprints", "ux", "static", "js")
    if not js_folder.exists():
        logger.error("Could not find static JS folder!")
        return

    for file in js_folder.glob("*.js"):
        if file.name.startswith("root."):
            split = file.name.split(".")
            if len(split) == 2:
                return

            app.cached_bundle_hash = split[1]
            values["filename"] = f"js/root.{app.cached_bundle_hash}.js"
            return


@app.before_serving
async def setup_db() -> None:
    """
    Creates a database pool for database interaction.
    """
    async with app.acquire_db() as con:
        logger.debug("VACUUMing database...")
        await con.execute("VACUUM;")
        logger.debug("Database VACUUM'd.")

        users = await con.fetchval(
            """
            SELECT
                COUNT(*)
            FROM
                users;
        """
        )

        locale = await con.fetchval(
            """
            SELECT
                locale
            FROM
                general_config;
        """
        )
        app.flags.LOCALE = locale

    if not users:
        logger.warning(
            "No existing users! Opening the app will result in a one-time registration page. Alternatively, you can create a user with the `tsundoku --create-user` command."
        )
        app.flags.IS_FIRST_LAUNCH = True


@app.before_serving
async def setup_session() -> None:
    """
    Creates an aiohttp ClientSession on startup using Quart's event loop.
    """
    loop = asyncio.get_event_loop()

    jar = aiohttp.CookieJar(
        unsafe=True
    )  # unsafe has to be True to store cookies from non-DNS URLs, i.e local IPs.

    logger.debug("Creating aiohttp ClientSession...")
    app.session = aiohttp.ClientSession(
        loop=loop, cookie_jar=jar, timeout=aiohttp.ClientTimeout(total=15.0)
    )
    logger.debug("Creating interface to downloader client...")
    app.dl_client = Manager(app.app_context(), app.session)

    res = await app.dl_client.test_client()
    app.flags.DL_CLIENT_CONNECTION_ERROR = not res


@app.before_serving
async def setup_tasks() -> None:
    """
    Creates the instances for the following tasks:
    poller, downloader, encoder

    These tasks are added to the app's global task list.
    """
    logger.debug("Starting APScheduler...")
    app.scheduler.start()

    app.scheduler.add_job(check_for_updates, CronTrigger.from_crontab("* 4 * * *"))

    async def poller() -> None:
        app.poller = Poller(app.app_context())
        await app.poller.start()

    async def downloader() -> None:
        app.downloader = Downloader(app.app_context())
        await app.downloader.start()

    async def encoder() -> None:
        app.encoder = Encoder(app.app_context())
        await app.encoder.resume()

    logger.debug("Starting task: Poller")
    app._tasks.append(asyncio.create_task(poller(), name="Poller"))
    logger.debug("Starting task: Downloader")
    app._tasks.append(asyncio.create_task(downloader(), name="Downloader"))
    logger.debug("Starting task: Encoder")
    app._tasks.append(asyncio.create_task(encoder(), name="Encoder"))

    logger.debug("All tasks created.")


@app.after_serving
async def cleanup() -> None:
    """
    Attempts to cancel any running tasks and close the aiohttp session.
    """
    failed_to_cancel = 0
    logger.debug("Cleanup: Attempting to cancel tasks...")
    app.scheduler.shutdown()

    for task in app._tasks:
        logger.debug(f"Cleanup: Attempting to cancel task '{task.get_name()}'...")
        try:
            task.cancel()
        except Exception:
            logger.warning(f"Could not cancel task '{task.get_name()}'!", exc_info=True)
            failed_to_cancel += 1
        else:
            logger.debug(f"Cleanup: Task '{task.get_name()}' cancelled.")

    logger.debug(f"Cleanup: Tasks cancelled. [{failed_to_cancel} failed to cancel]")

    logger.debug("Cleanup: Closing aiohttp session...")
    try:
        await app.session.close()
    except Exception:
        logger.warning("Cleanup: Could not close aiohttp session!", exc_info=True)
    else:
        logger.debug("Cleanup: aiohttp session closed.")


@ux_blueprint.context_processor
async def insert_locale() -> dict:
    return {"LOCALE": app.flags.LOCALE}


app.register_blueprint(api_blueprint)
app.register_blueprint(ux_blueprint)


def get_bind() -> Tuple[str, int]:
    """
    Returns the host and port bindings
    to run the app on.

    Returns
    -------
    Tuple[str, int]
        Address and port
    """
    cfg = GeneralConfig.sync_retrieve(app, ensure_exists=True)

    host = os.getenv("HOST", default="") if os.getenv("HOST") else cfg.host
    port = os.getenv("PORT", default="") if os.getenv("PORT") else cfg.port

    if isinstance(port, str) and not port.isdigit():
        raise ValueError("Port must be a number!")

    port = int(port)
    if not 0 < port < 65536:
        raise ValueError("Port must be between [1, 65536)!")

    return host, port


async def run() -> None:
    await migrate()
    setup_logging(app)

    host, port = get_bind()
    logger.debug(f"Attempting to bind to {host}:{port}")

    await app.run_task(host=host, port=port)
