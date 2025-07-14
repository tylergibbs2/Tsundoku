from pathlib import Path
import random
import string
from typing import Any, TypedDict, cast


class MockRSSFeed(TypedDict):
    items: list["MockRSSFeedItem"]


class MockRSSFeedItem(TypedDict):
    title: str
    link: str


BASE32_CHARSET = string.ascii_letters + "234567"


def generate_fake_magnet() -> str:
    return "magnet:?xt=urn:btih:" + "".join(random.choices(BASE32_CHARSET, k=random.choice([40, 32])))


def mock_feedparser_parse(*_: Any, **__: Any) -> MockRSSFeed:
    with Path("tests/mock/_rss_item_titles.txt").open("r", encoding="utf-8") as fd:
        titles = [line.strip() for line in fd.readlines() if line]

    return cast(MockRSSFeed, {"items": [{"title": title, "link": generate_fake_magnet()} for title in titles]})
