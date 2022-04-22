import asyncio
import datetime
import importlib
import importlib.util
import logging
import os
import secrets
from asyncio.events import AbstractEventLoop
from asyncio.queues import Queue
from typing import Any, Tuple, Union
from uuid import uuid4

import aiohttp
from argon2 import PasswordHasher
from quart import Quart, redirect, url_for
from quart_auth import AuthManager, Unauthorized
from werkzeug import Response

import tsundoku.asqlite
import tsundoku.exceptions as exceptions
import tsundoku.git as git
from tsundoku.blueprints.api import api_blueprint
from tsundoku.blueprints.ux import ux_blueprint
from tsundoku.config import GeneralConfig
from tsundoku.database import acquire, migrate, sync_acquire
from tsundoku.dl_client import Manager
from tsundoku.feeds import Downloader, Encoder, Poller
from tsundoku.log import setup_logging
from tsundoku.user import User

hasher = PasswordHasher()

auth = AuthManager()
auth.user_class = User

app: Any = Quart("Tsundoku", static_folder=None)

app.seen_titles = set()
app.connected_websockets = set()
app._tasks = []
logger = logging.getLogger("tsundoku")


class QuartConfig:
    SECRET_KEY = secrets.token_urlsafe(16)
    QUART_AUTH_COOKIE_SECURE = False


app.config.from_object(QuartConfig())
setup_logging(app)


async def insert_user(username: str, password: str) -> None:
    await migrate()

    if os.getenv("IS_DOCKER"):
        fp = "data/tsundoku.db"
    else:
        fp = "tsundoku.db"

    pw_hash = hasher.hash(password)
    async with tsundoku.asqlite.connect(fp) as con:
        await con.execute("""
            INSERT INTO
                users
                (username, password_hash, api_key)
            VALUES
                (?, ?, ?);
        """, username, pw_hash, str(uuid4()))


@app.errorhandler(Unauthorized)
async def redirect_to_login(*_: Any) -> Response:
    return redirect(url_for("ux.login"))


@app.before_serving
async def setup_db() -> None:
    """
    Creates a database pool for PostgreSQL interaction.
    """
    await migrate()
    app.acquire_db = acquire
    app.sync_acquire_db = sync_acquire

    async with app.acquire_db() as con:
        await con.execute("""
            SELECT
                COUNT(*)
            FROM
                users;
        """)
        users = await con.fetchval()

    if not users:
        logger.error("No existing users! Run `tsundoku --create-user` to create a new user.")



@app.before_request
async def update_check_needed() -> None:
    """
    Compares the time between now and the
    last update check. If it has been more
    than 1 day, check for an update.
    """
    cfg = await GeneralConfig.retrieve(app)
    if not cfg["update_do_check"]:
        return

    next_ = app.last_update_check + datetime.timedelta(hours=24)
    if next_ < datetime.datetime.utcnow():
        await git.check_for_updates()
        app.last_update_check = datetime.datetime.utcnow()


@app.before_serving
async def setup_session() -> None:
    """
    Creates an aiohttp ClientSession on startup using Quart's event loop.
    """
    loop = asyncio.get_event_loop()

    jar = aiohttp.CookieJar(unsafe=True)  # unsafe has to be True to store cookies from non-DNS URLs, i.e local IPs.

    app.session = aiohttp.ClientSession(
        loop=loop,
        cookie_jar=jar,
        timeout=aiohttp.ClientTimeout(total=15.0)
    )
    app.dl_client = Manager(app.session)

    app.update_info = []
    await git.check_for_updates()
    app.last_update_check = datetime.datetime.utcnow()


def _load_parsers() -> None:
    """
    Load all of the custom RSS parsers into the app.
    """
    app.rss_parsers = []

    required_attrs = (
        "name",
        "url",
        "version",
        "get_show_name",
        "get_episode_number"
    )

    for parser in ("parsers.subsplease",):
        spec: Any = importlib.util.find_spec(parser)

        if spec is None:
            logger.error(f"Parser `{parser}` Not Found")
            raise exceptions.ParserNotFound(parser)

        lib = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(lib)
        except Exception:
            logger.error(f"Parser `{parser}` Failed")
            continue

        try:
            setup = getattr(lib, "setup")
        except AttributeError:
            logger.error(f"Parser `{parser}` Missing Setup Function")
            continue

        try:
            new_context = app.app_context()
            parser_object = setup(new_context.app)
            for func in required_attrs:
                if not hasattr(parser_object, func):
                    logger.error(f"Parser `{parser}` missing attr/function `{func}`")
                    continue
            app.rss_parsers.append(parser_object)
        except Exception as e:
            logger.error(f"Parser `{parser}` Failed: {e}")
            continue

        logger.info("Loaded Parser `{0.name} v{0.version}`".format(parser_object))


@app.before_serving
async def load_parsers() -> None:
    """
    Load all of the custom RSS parsers into the app.
    """
    # It's okay if we're blocking here.
    # The webserver isn't intended to
    # be serving at this point in time.
    _load_parsers()


@app.before_serving
async def setup_tasks() -> None:
    """
    Creates the instances for the following tasks:
    poller, downloader, encoder

    These tasks are added to the app's global task list.
    """

    async def poller() -> None:
        app.poller = Poller(app.app_context())
        await app.poller.start()

    async def downloader() -> None:
        app.downloader = Downloader(app.app_context())
        await app.downloader.start()

    async def encoder() -> None:
        app.encoder = Encoder(app.app_context())
        await app.encoder.resume()

    app._tasks.append(asyncio.create_task(poller()))
    app._tasks.append(asyncio.create_task(downloader()))
    app._tasks.append(asyncio.create_task(encoder()))


@app.after_serving
async def cleanup() -> None:
    """
    Closes the database pool and the
    aiohttp ClientSession on script closure.

    Also tries to cancel running tasks (downloader and poller).
    """
    for task in app._tasks:
        try:
            task.cancel()
        except Exception:
            pass

    try:
        await app.session.close()
    except Exception:
        pass


@ux_blueprint.context_processor
async def insert_locale() -> dict:
    # Inserts the user's locale into jinja2 variables.
    cfg = await GeneralConfig.retrieve()

    return {"LOCALE": cfg["locale"]}


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
    cfg = GeneralConfig.sync_retrieve(ensure_exists=True)
    return cfg["host"], cfg["port"]


def run() -> None:
    host, port = get_bind()

    loop: Union[asyncio.ProactorEventLoop, AbstractEventLoop]
    try:
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    except AttributeError:
        loop = asyncio.get_event_loop()

    app.logging_queue = Queue(loop=loop, maxsize=50)
    auth.init_app(app)
    app.run(
        host=host,
        port=port,
        use_reloader=True,
        loop=loop
    )
