import asyncio
import importlib

import aiohttp
import asyncpg
from quart import Quart

from tsundoku.config import get_config_value
from tsundoku.deluge import DelugeClient
import tsundoku.exceptions as exceptions
from tsundoku.feeds import Downloader
from tsundoku.feeds import Poller


app = Quart("Tsundoku")


@app.before_serving
async def setup_session():
    """
    Creates an aiohttp ClientSession on startup using Quart's event loop.
    """
    loop = asyncio.get_event_loop()

    jar = aiohttp.CookieJar(unsafe=True)  # unsafe has to be True to store cookies from non-DNS URLs, i.e local IPs.

    app.session = aiohttp.ClientSession(loop=loop, cookie_jar=jar)
    app.deluge = DelugeClient(app.session)


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
            raise exceptions.ParserNotFound(parser)

        lib = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(lib)
        except Exception as e:
            raise exceptions.ParserFailed(parser, e) from e

        try:
            setup = getattr(lib, "setup")
        except AttributeError:
            raise exceptions.ParserMissingSetup(parser)

        try:
            new_context = app.app_context()
            parser_object = setup(new_context.app)
            for func in required_functions:
                if not hasattr(parser_object, func):
                    raise exceptions.ParserMissingRequiredFunction(f"{parser}: missing {func}")
            app.rss_parsers.append(parser_object)
        except Exception as e:
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

    asyncio.ensure_future(bg_task())


@app.before_serving
async def setup_downloader():
    """
    Creates an instance of the downloader manager
    and starts it.
    """
    async def bg_task():
        app.downloader = Downloader(app.app_context())
        await app.downloader.start()

    asyncio.ensure_future(bg_task())


@app.route("/")
async def index():
    return "placeholder"


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
    app.run(host=host, port=port)