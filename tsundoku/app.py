import asyncio
import datetime
import importlib
import logging
from logging.config import dictConfig
import os
import secrets

from argon2 import PasswordHasher
import aiohttp
import asyncpg
from hypercorn.asyncio import serve
from hypercorn.config import Config
from quart import Quart, redirect, url_for
from quart_auth import AuthManager, Unauthorized

from tsundoku.blueprints.ux import ux_blueprint
from tsundoku.blueprints.api import api_blueprint
from tsundoku.config import get_config_value
from tsundoku.dl_client import Manager
import tsundoku.exceptions as exceptions
from tsundoku.feeds import Downloader, Poller
import tsundoku.git as git
from tsundoku.user import User


hasher = PasswordHasher()

auth = AuthManager()
auth.user_class = User

app = Quart("Tsundoku", static_folder=None)

app.register_blueprint(api_blueprint)
app.register_blueprint(ux_blueprint)

app.seen_titles = set()
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
            "level": "DEBUG",
            "formatter": "default"
        },
        "file": {
            "filename": "tsundoku.log",
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "default",
            "encoding": "utf-8"
        }
    },
    "loggers": {
        "tsundoku": {
            "handlers": ["stream", "file"],
            "level": "DEBUG",
            "propagate": True
        }
    }
})


async def insert_user(username: str, password: str):
    host = get_config_value("PostgreSQL", "host")
    port = get_config_value("PostgreSQL", "port")
    user = get_config_value("PostgreSQL", "user")
    db_password = get_config_value("PostgreSQL", "password")
    database = get_config_value("PostgreSQL", "database")

    con = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=db_password,
        database=database
    )

    pw_hash = hasher.hash(password)

    await con.execute("""
        INSERT INTO
            users
            (username, password_hash)
        VALUES
            ($1, $2);
    """, username, pw_hash)

    await con.close()


@app.errorhandler(Unauthorized)
async def redirect_to_login(*_):
    return redirect(url_for("ux.login"))


@app.before_request
async def update_check_needed():
    """
    Compares the time between now and the
    last update check. If it has been more
    than 1 day, check for an update.
    """
    is_docker = os.environ.get("IS_DOCKER", False)
    should_we = get_config_value("Tsundoku", "do_update_checks")
    if is_docker or not should_we:
        return

    every = get_config_value("Tsundoku", "check_every_n_days")
    frequency = 24 * every

    next_ = app.last_update_check + datetime.timedelta(hours=frequency)
    if next_ < datetime.datetime.utcnow():
        git.check_for_updates()
        app.last_update_check = datetime.datetime.utcnow()


@app.before_serving
async def setup_session():
    """
    Creates an aiohttp ClientSession on startup using Quart's event loop.
    """
    loop = asyncio.get_event_loop()

    jar = aiohttp.CookieJar(unsafe=True)  # unsafe has to be True to store cookies from non-DNS URLs, i.e local IPs.

    app.session = aiohttp.ClientSession(loop=loop, cookie_jar=jar)
    app.dl_client = Manager(app.session)

    app.update_info = []
    git.check_for_updates()
    app.last_update_check = datetime.datetime.utcnow()


@app.before_serving
async def setup_db():
    """
    Creates a database pool for PostgreSQL interaction.
    """
    host = get_config_value("PostgreSQL", "host")
    port = get_config_value("PostgreSQL", "port")
    user = get_config_value("PostgreSQL", "user")
    password = get_config_value("PostgreSQL", "password")
    database = get_config_value("PostgreSQL", "database")

    loop = asyncio.get_event_loop()

    app.db_pool = await asyncpg.create_pool(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        loop=loop
    )

    async with app.db_pool.acquire() as con:
        users = await con.fetchval("""
            SELECT
                COUNT(*)
            FROM
                users;
        """)

    if not users:
        logger.error("No existing users! Run `tsundoku --create-user` to create a new user.")


@app.before_serving
async def load_parsers():
    """
    Load all of the custom RSS parsers into the app.
    """
    parsers = [f"parsers.{p}" for p in get_config_value("Tsundoku", "parsers")]
    app.rss_parsers = []

    required_functions = [
        "get_show_name",
        "get_episode_number"
    ]

    for parser in parsers:
        spec = importlib.util.find_spec(parser)
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
            for func in required_functions:
                if not hasattr(parser_object, func):
                    logger.error(f"Parser '{parser}' Missing {func}")
                    raise exceptions.ParserMissingRequiredFunction(f"{parser}: missing {func}")
            app.rss_parsers.append(parser_object)
        except Exception as e:
            logger.error(f"Parser '{parser}' Failed: {e}")
            raise exceptions.ParserFailed(parser, e) from e


@app.before_serving
async def setup_poller():
    """
    Creates in instance of the polling manager
    and starts it.
    """
    async def bg_task():
        app.poller = Poller(app.app_context())
        await app.poller.start()

    asyncio.create_task(bg_task())


@app.before_serving
async def setup_downloader():
    """
    Creates an instance of the downloader manager
    and starts it.
    """
    async def bg_task():
        app.downloader = Downloader(app.app_context())
        await app.downloader.start()

    asyncio.create_task(bg_task())


@app.after_serving
async def cleanup():
    """
    Closes the database pool and the
    aiohttp ClientSession on script closure.
    """
    await app.db_pool.close()
    await app.session.close()


host = get_config_value("Tsundoku", "host")
port = get_config_value("Tsundoku", "port")

def run():
    auth.init_app(app)

    if os.environ.get("IS_DOCKER", False):
        git.migrate()

    app.run(host=host, port=port, use_reloader=True)
