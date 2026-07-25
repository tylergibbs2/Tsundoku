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
        titles = [line.strip() for line in fd if line]

    return cast(MockRSSFeed, {"items": [{"title": title, "link": generate_fake_magnet()} for title in titles]})


class MockNyaaEntry(TypedDict):
    title: str
    published: str
    link: str
    id: str
    nyaa_size: str
    nyaa_seeders: str
    nyaa_leechers: str


class MockNyaaFeed(TypedDict):
    entries: list[MockNyaaEntry]


#: ``SearchResult.from_dict`` parses this with "%a, %d %b %Y %H:%M:%S %z".
NYAA_PUBLISHED = "Mon, 06 Nov 2023 12:00:00 +0000"


def make_nyaa_entry(
    title: str,
    *,
    link: str | None = None,
    published: str = NYAA_PUBLISHED,
    size: str = "1.4 GiB",
    seeders: int = 100,
    leechers: int = 5,
) -> MockNyaaEntry:
    """Build one entry shaped like nyaa.si's RSS output.

    Distinct from :func:`mock_feedparser_parse`, which mimics the generic
    release feeds the poller consumes: nyaa's feed is read from ``entries``
    rather than ``items`` and carries the extra ``nyaa_*`` fields that
    ``SearchResult.from_dict`` requires.
    """
    return {
        "title": title,
        "published": published,
        "link": link if link is not None else generate_fake_magnet(),
        "id": f"https://nyaa.si/view/{abs(hash(title)) % 1_000_000}",
        "nyaa_size": size,
        "nyaa_seeders": str(seeders),
        "nyaa_leechers": str(leechers),
    }


def mock_nyaa_feed(titles: list[str]) -> MockNyaaFeed:
    """A parsed nyaa.si search feed containing one entry per title."""
    return {"entries": [make_nyaa_entry(title) for title in titles]}
