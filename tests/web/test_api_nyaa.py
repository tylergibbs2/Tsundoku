from copy import deepcopy
from typing import Any

import httpx
import pytest

from tests.mock import MockTsundokuAppState, make_nyaa_entry, mock_nyaa_feed

from .envelope import API, error, success

#: A .torrent URL, matching what the nyaa searcher actually yields -- its RSS
#: <link> is always https://nyaa.si/download/<id>.torrent. These tests used to
#: use a magnet here and register multi-file structures against it, which no
#: real magnet can describe: a magnet carries an info hash and at most a
#: display name, never a file list.
TORRENT = "https://nyaa.si/download/1234567.torrent"


def install_feed(monkeypatch: pytest.MonkeyPatch, feed: Any) -> None:
    monkeypatch.setattr("feedparser.parse", lambda *_, **__: deepcopy(feed))


# ---------------------------------------------------------------------------
# GET /nyaa - searching
# ---------------------------------------------------------------------------


async def test_search_without_a_query_returns_nothing(client: httpx.AsyncClient) -> None:
    """No query means an empty result, not an error or a full listing."""
    assert success(await client.get(f"{API}/nyaa")) == []


async def test_search_returns_results(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    install_feed(
        monkeypatch,
        {"entries": [make_nyaa_entry("[SubsPlease] Chainsaw Man - 01 (1080p) [ABCD].mkv", size="1.4 GiB", seeders=42)]},
    )

    result = success(await client.get(f"{API}/nyaa", params={"query": "chainsaw man"}))

    assert len(result) == 1
    assert result[0]["title"] == "[SubsPlease] Chainsaw Man - 01 (1080p) [ABCD].mkv"
    assert result[0]["size"] == "1.4 GiB"
    assert result[0]["seeders"] == 42


async def test_search_respects_limit(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    install_feed(monkeypatch, mock_nyaa_feed([f"[Group] Show - {n:02d} (1080p).mkv" for n in range(1, 11)]))

    result = success(await client.get(f"{API}/nyaa", params={"query": "show", "limit": 3}))

    assert len(result) == 3


async def test_search_failure_becomes_a_400(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*_: Any, **__: Any) -> Any:
        raise RuntimeError("nyaa is down")

    monkeypatch.setattr("feedparser.parse", explode)

    response = await client.get(f"{API}/nyaa", params={"query": "chainsaw"})

    assert error(response, 400) == "Error searching for the specified query."


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"page": 0}])
async def test_search_rejects_out_of_range_paging(client: httpx.AsyncClient, params: dict) -> None:
    response = await client.get(f"{API}/nyaa", params={"query": "x", **params})

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /nyaa - adding a result
# ---------------------------------------------------------------------------


async def test_add_result_creates_entries(client: httpx.AsyncClient, app: MockTsundokuAppState) -> None:
    app.dl_client.set_file_structure(
        TORRENT,
        ["[Group] Chainsaw Man - 01 (1080p).mkv", "[Group] Chainsaw Man - 02 (1080p).mkv"],
    )

    result = success(await client.post(f"{API}/nyaa", json={"show_id": 1, "torrent_link": TORRENT}))

    assert [entry["episode"] for entry in result] == [1, 2]
    assert all(entry["state"] == "downloading" for entry in result)


async def test_add_result_queues_the_torrent(client: httpx.AsyncClient, app: MockTsundokuAppState) -> None:
    app.dl_client.set_file_structure(TORRENT, ["[Group] Chainsaw Man - 01 (1080p).mkv"])

    await client.post(f"{API}/nyaa", json={"show_id": 1, "torrent_link": TORRENT})

    assert len(app.dl_client.torrents) == 1


async def test_add_result_for_unknown_show_is_404(client: httpx.AsyncClient) -> None:
    response = await client.post(f"{API}/nyaa", json={"show_id": 9999, "torrent_link": TORRENT})

    assert error(response, 404) == "Show ID does not exist in the database."


async def test_add_result_skips_existing_episodes(client: httpx.AsyncClient, app: MockTsundokuAppState) -> None:
    async with app.acquire_db() as con:
        await con.execute("INSERT INTO show_entry (show_id, episode, current_state, torrent_hash) VALUES (1, 1, 'completed', 'old');")
    app.dl_client.set_file_structure(
        TORRENT,
        ["[Group] Chainsaw Man - 01 (1080p).mkv", "[Group] Chainsaw Man - 02 (1080p).mkv"],
    )

    result = success(await client.post(f"{API}/nyaa", json={"show_id": 1, "torrent_link": TORRENT}))

    assert [entry["episode"] for entry in result] == [2]


async def test_add_result_with_overwrite_replaces_existing(client: httpx.AsyncClient, app: MockTsundokuAppState) -> None:
    async with app.acquire_db() as con:
        await con.execute("INSERT INTO show_entry (show_id, episode, current_state, torrent_hash) VALUES (1, 1, 'completed', 'old');")
    app.dl_client.set_file_structure(TORRENT, ["[Group] Chainsaw Man - 01 (1080p).mkv"])

    result = success(await client.post(f"{API}/nyaa", json={"show_id": 1, "torrent_link": TORRENT, "overwrite": True}))

    assert [entry["episode"] for entry in result] == [1]

    async with app.acquire_db() as con:
        count = await con.fetchval("SELECT COUNT(*) FROM show_entry WHERE show_id=1 AND episode=1;")

    assert count == 1, "overwrite should replace the entry, not duplicate it"


@pytest.mark.parametrize("body", [{}, {"show_id": 1}, {"torrent_link": TORRENT}])
async def test_add_result_rejects_incomplete_body(client: httpx.AsyncClient, body: dict) -> None:
    response = await client.post(f"{API}/nyaa", json=body)

    assert response.status_code == 422
