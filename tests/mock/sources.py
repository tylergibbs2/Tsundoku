from collections.abc import AsyncGenerator
import json

from tsundoku.sources import Source

MOCK_SOURCE = """
{
  "name": "Mock Source",
  "version": "1.0.0",
  "url": "https://mock.com/rss/",
  "rssItemKeyMapping": {
    "filename": "$.title",
    "torrent": "$.link"
  }
}
"""


async def mock_get_all_sources() -> AsyncGenerator[Source, None]:  # noqa: RUF029
    yield Source.from_object(json.loads(MOCK_SOURCE))
