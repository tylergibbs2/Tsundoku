import asyncio

import feedparser
from quart.ctx import AppContext


async def get_feed_from_parser(app, parser):
    loop = asyncio.get_running_loop()
    feed_object = await loop.run_in_executor(None, feedparser.parse, parser.url)
    return feed_object["feed"]


async def check_feed(feed: dict):
    print(feed["title"])


async def feed_poller(app_context: AppContext):
    app = app_context.app

    while True:
        for parser in app.rss_parsers:
            feed = await get_feed_from_parser(app, parser)
            await check_feed(feed)

        await asyncio.sleep(5)
