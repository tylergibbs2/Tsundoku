import asyncio
import datetime
import importlib
import importlib.util
import logging
import os
import secrets
from asyncio.events import AbstractEventLoop
from logging.config import dictConfig
from typing import Any, Union
from uuid import uuid4

import aiohttp
from argon2 import PasswordHasher
from quart import Quart, redirect, url_for
from quart.wrappers.response import Response
from quart_auth import AuthManager, Unauthorized

import tsundoku.asqlite
import tsundoku.exceptions as exceptions
import tsundoku.git as git
from tsundoku.blueprints.api import api_blueprint
from tsundoku.blueprints.ux import ux_blueprint
from tsundoku.config import get_config_value
from tsundoku.database import acquire, migrate
from tsundoku.dl_client import Manager
from tsundoku.feeds import Downloader, Poller
from tsundoku.feeds.encoder import Encoder
from tsundoku.user import User

hasher = PasswordHasher()

auth = AuthManager()
auth.user_class = User

app: Any = Quart("Tsundoku", static_folder=None)

app.seen_titles = set()
app._tasks = []
logger = logging.getLogger("tsundoku")


class QuartConfig:
    SECRET_KEY = secrets.token_urlsafe(16)
    QUART_AUTH_COOKIE_SECURE = False


app.config.from_object(QuartConfig())


dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    },
    "handlers": {
        "stream": {
            "class": "logging.StreamHandler",
            "formatter": "default"
        },
        "file": {
            "filename": "tsundoku.log",
            "class": "logging.FileHandler",
            "formatter": "default",
            "encoding": "utf-8"
        }
    },
    "loggers": {
        "tsundoku": {
            "handlers": ["stream", "file"],
            "level": get_config_value("Tsundoku", "log_level", default="info").upper(),
            "propagate": True
        }
    }
})


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


@app.before_request
async def update_check_needed() -> None:
    """
    Compares the time between now and the
    last update check. If it has been more
    than 1 day, check for an update.
    """
    should_we = get_config_value("Tsundoku", "do_update_checks")
    if not should_we:
        return

    every = get_config_value("Tsundoku", "check_every_n_days")
    frequency = 24 * every

    next_ = app.last_update_check + datetime.timedelta(hours=frequency)
    if next_ < datetime.datetime.utcnow():
        git.check_for_updates()
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
    git.check_for_updates()
    app.last_update_check = datetime.datetime.utcnow()


@app.before_serving
async def setup_db() -> None:
    """
    Creates a database pool for PostgreSQL interaction.
    """
    await migrate()
    app.acquire_db = acquire

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

    for parser in get_config_value("Tsundoku", "parsers"):
        spec: Any = importlib.util.find_spec(parser)

        if spec is None:
            logger.error(f"Parser '{parser}' Not Found")
            raise exceptions.ParserNotFound(parser)

        lib = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(lib)
        except Exception as e:
            logger.error(f"Parser '{parser}' Failed")
            raise exceptions.ParserFailed(parser, e) from e

        try:
            setup = getattr(lib, "setup")
        except AttributeError:
            logger.error(f"Parser '{parser}' Missing Setup Function")
            raise exceptions.ParserMissingSetup(parser)

        try:
            new_context = app.app_context()
            parser_object = setup(new_context.app)
            for func in required_attrs:
                if not hasattr(parser_object, func):
                    logger.error(f"Parser '{parser}' missing attr/function '{func}'")
                    raise exceptions.ParserMissingRequiredFunction(f"{parser}: missing attr/function '{func}'")
            app.rss_parsers.append(parser_object)
        except Exception as e:
            logger.error(f"Parser '{parser}' Failed: {e}")
            raise exceptions.ParserFailed(parser, e) from e

        logger.info("Loaded Parser {0.name} v{0.version}".format(parser_object))


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
async def setup_poller() -> None:
    """
    Creates in instance of the polling manager
    and starts it.
    """
    if not hasattr(app, "db_pool"):
        return

    async def bg_task() -> None:
        app.poller = Poller(app.app_context())
        await app.poller.start()

    app._tasks.append(asyncio.create_task(bg_task()))


@app.before_serving
async def setup_downloader() -> None:
    """
    Creates an instance of the downloader manager
    and starts it.
    """
    if not hasattr(app, "db_pool"):
        return

    async def bg_task() -> None:
        app.downloader = Downloader(app.app_context())
        await app.downloader.start()

    app._tasks.append(asyncio.create_task(bg_task()))


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
    locale = get_config_value("Tsundoku", "locale", default="en")

    return {"LOCALE": locale}


app.register_blueprint(api_blueprint)
app.register_blueprint(ux_blueprint)


def run() -> None:
    host = get_config_value("Tsundoku", "host")
    port = get_config_value("Tsundoku", "port")

    loop: Union[asyncio.ProactorEventLoop, AbstractEventLoop]
    try:
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    except AttributeError:
        loop = asyncio.get_event_loop()

    auth.init_app(app)
    app.run(
        host=host,
        port=port,
        use_reloader=True,
        loop=loop
    )
