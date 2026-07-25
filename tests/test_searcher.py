from copy import deepcopy
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

from tests.mock import MockTsundokuAppState, UnregisteredTorrentError, make_nyaa_entry, mock_nyaa_feed
from tsundoku.nyaa import NyaaSearcher, SearchResult
from tsundoku.utils import parse_anime_title

TORRENT = "magnet:?xt=urn:btih:aabbcc112233"


def install_feed(monkeypatch: pytest.MonkeyPatch, feed: Any) -> list[str]:
    """Point feedparser at ``feed`` and record the URLs it was asked for.

    A fresh copy is handed out per call, matching real feedparser. This is not
    incidental: ``SearchResult.from_dict`` builds itself with ``_from.pop()``,
    so it strips the entry dict it is given. Serving the same object twice
    would yield entries with no title on the second search.
    """
    requested: list[str] = []

    def _parse(url: str, *_: Any, **__: Any) -> Any:
        requested.append(url)
        return deepcopy(feed)

    monkeypatch.setattr("feedparser.parse", _parse)
    return requested


# ---------------------------------------------------------------------------
# Query construction
# ---------------------------------------------------------------------------


def test_query_url_targets_the_anime_category() -> None:
    url = NyaaSearcher._get_query_url("chainsaw man")
    params = parse_qs(urlparse(url).query)

    assert urlparse(url).netloc == "nyaa.si"
    assert params["q"] == ["chainsaw man"]
    assert params["c"] == ["1_2"]  # anime - english translated
    assert params["s"] == ["seeders"]
    assert params["o"] == ["desc"]


def test_query_url_escapes_special_characters() -> None:
    url = NyaaSearcher._get_query_url("re:zero & co")

    assert " " not in url
    assert parse_qs(urlparse(url).query)["q"] == ["re:zero & co"]


# ---------------------------------------------------------------------------
# Searching
# ---------------------------------------------------------------------------


async def test_search_maps_feed_entries(app: MockTsundokuAppState, monkeypatch: pytest.MonkeyPatch) -> None:
    feed = {"entries": [make_nyaa_entry("[SubsPlease] Chainsaw Man - 01 (1080p) [ABCD1234].mkv", size="1.4 GiB", seeders=42, leechers=7)]}
    install_feed(monkeypatch, feed)

    results = await NyaaSearcher.search(app, "chainsaw man")

    assert len(results) == 1
    assert results[0].title == "[SubsPlease] Chainsaw Man - 01 (1080p) [ABCD1234].mkv"
    assert results[0].size == "1.4 GiB"
    assert results[0].seeders == 42
    assert results[0].leechers == 7
    assert results[0].published.year == 2023
    assert results[0].show_id is None


async def test_search_passes_the_query_through(app: MockTsundokuAppState, monkeypatch: pytest.MonkeyPatch) -> None:
    requested = install_feed(monkeypatch, mock_nyaa_feed([]))

    await NyaaSearcher.search(app, "spy family")

    assert len(requested) == 1
    assert parse_qs(urlparse(requested[0]).query)["q"] == ["spy family"]


async def test_search_paginates(app: MockTsundokuAppState, monkeypatch: pytest.MonkeyPatch) -> None:
    titles = [f"[Group] Show - {n:02d} (1080p).mkv" for n in range(1, 11)]
    install_feed(monkeypatch, mock_nyaa_feed(titles))

    first = await NyaaSearcher.search(app, "show", limit=4, page=1)
    second = await NyaaSearcher.search(app, "show", limit=4, page=2)
    third = await NyaaSearcher.search(app, "show", limit=4, page=3)

    assert [r.title for r in first] == titles[:4]
    assert [r.title for r in second] == titles[4:8]
    assert [r.title for r in third] == titles[8:]


async def test_search_page_beyond_the_end_is_empty(app: MockTsundokuAppState, monkeypatch: pytest.MonkeyPatch) -> None:
    install_feed(monkeypatch, mock_nyaa_feed(["[Group] Show - 01 (1080p).mkv"]))

    assert await NyaaSearcher.search(app, "show", limit=10, page=5) == []


async def test_search_skips_entries_with_non_string_titles(app: MockTsundokuAppState, monkeypatch: pytest.MonkeyPatch) -> None:
    good = make_nyaa_entry("[Group] Show - 01 (1080p).mkv")
    bad = {**make_nyaa_entry("placeholder"), "title": None}
    install_feed(monkeypatch, {"entries": [bad, good]})

    results = await NyaaSearcher.search(app, "show")

    assert [r.title for r in results] == ["[Group] Show - 01 (1080p).mkv"]


async def test_search_skips_unparseable_titles(app: MockTsundokuAppState, monkeypatch: pytest.MonkeyPatch) -> None:
    """A title anitomy chokes on is dropped, not fatal to the whole search."""
    install_feed(monkeypatch, mock_nyaa_feed(["unparseable", "[Group] Show - 01 (1080p).mkv"]))

    def selectively_explode(title: str) -> Any:
        if title == "unparseable":
            raise ValueError("anitomy exploded")
        return parse_anime_title(title)

    monkeypatch.setattr("tsundoku.nyaa.searcher.parse_anime_title", selectively_explode)

    results = await NyaaSearcher.search(app, "show")

    assert [r.title for r in results] == ["[Group] Show - 01 (1080p).mkv"]


# ---------------------------------------------------------------------------
# get_episodes
# ---------------------------------------------------------------------------


async def test_get_episodes_from_a_folder_torrent(app: MockTsundokuAppState) -> None:
    app.dl_client.set_file_structure(
        TORRENT,
        [
            "[Group] Chainsaw Man - 01 (1080p).mkv",
            "[Group] Chainsaw Man - 02 (1080p).mkv",
            "[Group] Chainsaw Man - 03 (1080p).mkv",
        ],
    )
    result = SearchResult.from_necessary(app, 1, TORRENT)

    assert await result.get_episodes() == [1, 2, 3]


async def test_get_episodes_from_a_single_file_torrent(app: MockTsundokuAppState) -> None:
    app.dl_client.set_file_structure(TORRENT, ["[Group] Chainsaw Man - 07 (1080p).mkv"])
    result = SearchResult.from_necessary(app, 1, TORRENT)

    assert await result.get_episodes() == [7]


async def test_get_episodes_ignores_files_without_an_episode_number(app: MockTsundokuAppState) -> None:
    app.dl_client.set_file_structure(
        TORRENT,
        ["[Group] Chainsaw Man - 01 (1080p).mkv", "readme.txt", "[Group] Chainsaw Man - NCOP (1080p).mkv"],
    )
    result = SearchResult.from_necessary(app, 1, TORRENT)

    assert await result.get_episodes() == [1]


async def test_get_episodes_on_unregistered_torrent_is_loud(app: MockTsundokuAppState) -> None:
    """A missing fixture must not masquerade as "this torrent has no episodes"."""
    result = SearchResult.from_necessary(app, 1, "magnet:?xt=urn:btih:unknown")

    with pytest.raises(UnregisteredTorrentError):
        await result.get_episodes()


# ---------------------------------------------------------------------------
# process
# ---------------------------------------------------------------------------


async def entry_rows(app: MockTsundokuAppState, show_id: int) -> list[tuple]:
    async with app.acquire_db() as con:
        rows = await con.fetchall(
            "SELECT episode, torrent_hash, current_state FROM show_entry WHERE show_id=? ORDER BY episode;",
            show_id,
        )
    return [(row["episode"], row["torrent_hash"], row["current_state"]) for row in rows]


async def test_process_adds_every_episode(app: MockTsundokuAppState) -> None:
    app.dl_client.set_file_structure(
        TORRENT,
        ["[Group] Chainsaw Man - 01 (1080p).mkv", "[Group] Chainsaw Man - 02 (1080p).mkv"],
    )
    result = SearchResult.from_necessary(app, 1, TORRENT)

    added = await result.process()

    assert [entry.episode for entry in added] == [1, 2]
    assert all(entry.state == "downloading" for entry in added)
    assert [(episode, state) for episode, _, state in await entry_rows(app, 1)] == [(1, "downloading"), (2, "downloading")]


async def test_process_adds_the_torrent_to_the_download_client(app: MockTsundokuAppState) -> None:
    app.dl_client.set_file_structure(TORRENT, ["[Group] Chainsaw Man - 01 (1080p).mkv"])

    await SearchResult.from_necessary(app, 1, TORRENT).process()

    assert len(app.dl_client.torrents) == 1


async def test_process_marks_entries_as_manually_created(app: MockTsundokuAppState) -> None:
    app.dl_client.set_file_structure(TORRENT, ["[Group] Chainsaw Man - 01 (1080p).mkv"])

    await SearchResult.from_necessary(app, 1, TORRENT).process()

    async with app.acquire_db() as con:
        manual = await con.fetchval("SELECT created_manually FROM show_entry WHERE show_id=1;")

    assert manual


async def test_process_skips_episodes_that_already_exist(app: MockTsundokuAppState) -> None:
    async with app.acquire_db() as con:
        await con.execute("INSERT INTO show_entry (show_id, episode, current_state, torrent_hash) VALUES (1, 1, 'completed', 'old');")
    app.dl_client.set_file_structure(
        TORRENT,
        ["[Group] Chainsaw Man - 01 (1080p).mkv", "[Group] Chainsaw Man - 02 (1080p).mkv"],
    )

    added = await SearchResult.from_necessary(app, 1, TORRENT).process()

    assert [entry.episode for entry in added] == [2]
    assert "completed" in [state for _, _, state in await entry_rows(app, 1)]


async def test_process_is_a_noop_when_everything_exists(app: MockTsundokuAppState) -> None:
    async with app.acquire_db() as con:
        await con.execute("INSERT INTO show_entry (show_id, episode, current_state, torrent_hash) VALUES (1, 1, 'completed', 'old');")
    app.dl_client.set_file_structure(TORRENT, ["[Group] Chainsaw Man - 01 (1080p).mkv"])

    added = await SearchResult.from_necessary(app, 1, TORRENT).process()

    assert added == []
    assert app.dl_client.torrents == [], "no torrent should be queued when nothing is new"


async def test_process_overwrite_replaces_the_existing_entry(app: MockTsundokuAppState) -> None:
    async with app.acquire_db() as con:
        await con.execute("INSERT INTO show_entry (show_id, episode, current_state, torrent_hash) VALUES (1, 1, 'completed', 'oldhash');")
    app.dl_client.set_file_structure(TORRENT, ["[Group] Chainsaw Man - 01 (1080p).mkv"])

    added = await SearchResult.from_necessary(app, 1, TORRENT).process(overwrite=True)

    assert [entry.episode for entry in added] == [1]

    rows = await entry_rows(app, 1)
    assert len(rows) == 1, "the superseded entry should be gone, not duplicated"
    assert rows[0][1] != "oldhash"


async def test_process_without_a_show_id_adds_nothing(app: MockTsundokuAppState) -> None:
    result = SearchResult.from_necessary(app, 1, TORRENT)
    result.show_id = None

    assert await result.process() == []


async def test_process_handles_a_rejected_magnet(app: MockTsundokuAppState) -> None:
    """add_torrent returning None must not leave half-written entries behind."""
    link = "magnet:?xt=urn:btih:"  # no info hash for the client to extract
    app.dl_client.set_file_structure(link, ["[Group] Chainsaw Man - 01 (1080p).mkv"])

    added = await SearchResult.from_necessary(app, 1, link).process()

    assert added == []
    assert await entry_rows(app, 1) == []
