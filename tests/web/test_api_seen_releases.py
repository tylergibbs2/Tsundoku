from copy import deepcopy
from typing import Any

import httpx
import pytest
import pytest_asyncio

from tests.mock import MockTsundokuAppState, make_nyaa_entry

from .envelope import API, error, success

SEEDED = [
    # title, release_group, episode, resolution
    ("Chainsaw Man", "SubsPlease", 1, "1080p"),
    ("Chainsaw Man", "SubsPlease", 2, "1080p"),
    ("Chainsaw Man", "SubsPlease", 1, "720p"),
    ("Buddy Daddies", "Erai-raws", 1, "1080p"),
]


@pytest_asyncio.fixture(name="seen")
async def seen_fixture(app: MockTsundokuAppState) -> None:
    async with app.acquire_db() as con:
        for title, group, episode, resolution in SEEDED:
            await con.execute(
                """
                INSERT INTO seen_release (title, release_group, episode, resolution, torrent_destination)
                VALUES (?, ?, ?, ?, ?);
                """,
                title,
                group,
                episode,
                resolution,
                f"magnet:?xt=urn:btih:{title[:4]}{group[:4]}{episode}{resolution}".replace(" ", ""),
            )


def install_feed(monkeypatch: pytest.MonkeyPatch, feed: Any) -> None:
    monkeypatch.setattr("feedparser.parse", lambda *_, **__: deepcopy(feed))


# ---------------------------------------------------------------------------
# GET /seen_releases/filter
# ---------------------------------------------------------------------------


async def test_filter_returns_everything_when_unfiltered(client: httpx.AsyncClient, seen: None) -> None:
    result = success(await client.get(f"{API}/seen_releases/filter"))

    assert len(result) == len(SEEDED)


async def test_filter_by_title(client: httpx.AsyncClient, seen: None) -> None:
    result = success(await client.get(f"{API}/seen_releases/filter", params={"title": "Chainsaw Man"}))

    assert {release["title"] for release in result} == {"Chainsaw Man"}
    assert len(result) == 3


async def test_filter_by_resolution(client: httpx.AsyncClient, seen: None) -> None:
    result = success(await client.get(f"{API}/seen_releases/filter", params={"resolution": "720p"}))

    assert len(result) == 1
    assert result[0]["resolution"] == "720p"


async def test_filter_by_episode(client: httpx.AsyncClient, seen: None) -> None:
    result = success(await client.get(f"{API}/seen_releases/filter", params={"episode": 2}))

    assert [release["episode"] for release in result] == [2]


async def test_filter_combines_criteria(client: httpx.AsyncClient, seen: None) -> None:
    params = {"title": "Chainsaw Man", "release_group": "SubsPlease", "resolution": "1080p"}

    result = success(await client.get(f"{API}/seen_releases/filter", params=params))

    assert sorted(release["episode"] for release in result) == [1, 2]


async def test_filter_with_no_matches_is_empty(client: httpx.AsyncClient, seen: None) -> None:
    assert success(await client.get(f"{API}/seen_releases/filter", params={"title": "Nonexistent"})) == []


# ---------------------------------------------------------------------------
# GET /seen_releases/distinct
# ---------------------------------------------------------------------------


async def test_distinct_titles(client: httpx.AsyncClient, seen: None) -> None:
    result = success(await client.get(f"{API}/seen_releases/distinct", params={"field": "title"}))

    assert sorted(result) == ["Buddy Daddies", "Chainsaw Man"]


async def test_distinct_resolutions_scoped_by_title(client: httpx.AsyncClient, seen: None) -> None:
    params = {"field": "resolution", "title": "Chainsaw Man"}

    result = success(await client.get(f"{API}/seen_releases/distinct", params=params))

    assert sorted(result) == ["1080p", "720p"]


async def test_distinct_release_groups(client: httpx.AsyncClient, seen: None) -> None:
    result = success(await client.get(f"{API}/seen_releases/distinct", params={"field": "release_group"}))

    assert sorted(result) == ["Erai-raws", "SubsPlease"]


async def test_distinct_rejects_an_unknown_field(client: httpx.AsyncClient, seen: None) -> None:
    """The field name reaches SQL, so only an allow-list may pass."""
    response = await client.get(f"{API}/seen_releases/distinct", params={"field": "torrent_destination"})

    assert response.status_code == 400


async def test_distinct_rejects_injection_attempt(client: httpx.AsyncClient, seen: None) -> None:
    response = await client.get(f"{API}/seen_releases/distinct", params={"field": "title; DROP TABLE seen_release;--"})

    assert response.status_code == 400


async def test_distinct_requires_the_field_parameter(client: httpx.AsyncClient) -> None:
    assert (await client.get(f"{API}/seen_releases/distinct")).status_code == 422


# ---------------------------------------------------------------------------
# POST /seen_releases/add
# ---------------------------------------------------------------------------


async def test_add_persists_search_results(client: httpx.AsyncClient, seen: None, monkeypatch: pytest.MonkeyPatch) -> None:
    install_feed(
        monkeypatch,
        {"entries": [make_nyaa_entry(f"[SubsPlease] Chainsaw Man - {n:02d} (1080p) [ABCD].mkv") for n in (3, 4)]},
    )

    body = {"title": "Chainsaw Man", "release_group": "SubsPlease", "resolution": "1080p"}
    result = success(await client.post(f"{API}/seen_releases/add", json=body))

    assert result["additional"] == 2
    assert result["episodes"] == [1, 2, 3, 4]


async def test_add_reports_zero_when_nothing_is_new(client: httpx.AsyncClient, seen: None, monkeypatch: pytest.MonkeyPatch) -> None:
    install_feed(
        monkeypatch,
        {"entries": [make_nyaa_entry("[SubsPlease] Chainsaw Man - 01 (1080p) [ABCD].mkv")]},
    )

    body = {"title": "Chainsaw Man", "release_group": "SubsPlease", "resolution": "1080p"}
    result = success(await client.post(f"{API}/seen_releases/add", json=body))

    assert result["additional"] == 0
    assert result["episodes"] == [1, 2]


async def test_add_files_results_under_the_requested_title(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Results are re-keyed to the caller's title/group so a later add finds them."""
    install_feed(
        monkeypatch,
        {"entries": [make_nyaa_entry("[SomeoneElse] Chainsawman S01E05 (1080p).mkv")]},
    )

    body = {"title": "My Title", "release_group": "My Group", "resolution": "1080p"}
    success(await client.post(f"{API}/seen_releases/add", json=body))

    stored = success(await client.get(f"{API}/seen_releases/filter", params={"title": "My Title"}))

    assert stored
    assert {release["release_group"] for release in stored} == {"My Group"}


async def test_add_surfaces_search_failures(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*_: Any, **__: Any) -> Any:
        raise RuntimeError("nyaa is down")

    monkeypatch.setattr("feedparser.parse", explode)

    body = {"title": "Chainsaw Man", "release_group": "SubsPlease", "resolution": "1080p"}
    response = await client.post(f"{API}/seen_releases/add", json=body)

    assert error(response, 400) == "Error searching Nyaa for more releases."


@pytest.mark.parametrize("body", [{}, {"title": "x"}, {"title": "x", "release_group": "y"}])
async def test_add_rejects_incomplete_body(client: httpx.AsyncClient, body: dict) -> None:
    assert (await client.post(f"{API}/seen_releases/add", json=body)).status_code == 422
