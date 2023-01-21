from __future__ import annotations

import random
import string
from typing import List, TypedDict


class MockRSSFeed(TypedDict):
    items: List[MockRSSFeedItem]


class MockRSSFeedItem(TypedDict):
    title: str
    link: str


BASE32_CHARSET = string.ascii_letters + "234567"


def generate_fake_magnet() -> str:
    return "magnet:?xt=urn:btih:" + "".join(
        random.choices(BASE32_CHARSET, k=random.choice([40, 32]))
    )


def mock_feedparser_parse(*_, **__) -> MockRSSFeed:
    with open("tests/mock/_rss_item_titles.txt", "r", encoding="utf-8") as fp:
        titles = [line.strip() for line in fp.readlines() if line]

    return {
        "items": [{"title": title, "link": generate_fake_magnet()} for title in titles]
    }
