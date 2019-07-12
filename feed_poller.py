import asyncio

import feedparser
from quart.ctx import AppContext


async def get_feed_from_parser(parser):
    loop = asyncio.get_running_loop()
    feed_object = await loop.run_in_executor(None, feedparser.parse, parser.url)
    parser.feed = feed_object
    return parser


async def get_torrent_link(parser, item: dict):
    deluge = parser.app.deluge
    torrent_location = parser.get_link_location(item)

    return await deluge.get_magnet(torrent_location)


async def check_item(parser, item):
    if hasattr(parser, "ignore_logic"):
        if parser.ignore_logic(item) == False:
            return

    if hasattr(parser, "get_link_location"):
        torrent_url = await get_torrent_link(parser, item)
    else:
        torrent_url = item["link"]

    if hasattr(parser, "get_file_name"):
        torrent_name = parser.get_file_name(item)
    else:
        torrent_name = item["title"]


async def check_feed(parser):
    for item in parser.feed["items"]:
        await check_item(parser, item)


async def feed_poller(app_context: AppContext):
    app = app_context.app

    while True:
        for parser in app.rss_parsers:
            parser = await get_feed_from_parser(parser)
            await check_feed(parser)

        await asyncio.sleep(900)
