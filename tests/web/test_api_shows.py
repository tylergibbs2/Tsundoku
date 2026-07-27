import httpx
import pytest
import pytest_asyncio

from tests.mock import MockTsundokuAppState
from tsundoku.manager.kitsu import API_URL as KITSU_API_URL

from .envelope import API, error, success

ALL_STATUSES = "current,finished,tba,unreleased,upcoming"


@pytest.fixture(name="kitsu_offline", autouse=True)
def kitsu_offline_fixture(app: MockTsundokuAppState) -> None:
    """Answer Kitsu lookups with an empty result.

    Shows in the fixture data carry no cached kitsu_info row, so anything that
    materialises a Show reaches for the metadata API. These tests are about the
    HTTP layer, not metadata, so the lookup is stubbed out rather than removed.
    """
    app.session.stub("GET", KITSU_API_URL, json={"data": []})


@pytest_asyncio.fixture(name="with_statuses")
async def with_statuses_fixture(app: MockTsundokuAppState) -> None:
    """Give every fixture show a cached Kitsu status.

    The listing query joins on kitsu_info and requires a non-null show_status,
    so shows are invisible to it until they have been through metadata lookup.
    """
    async with app.acquire_db() as con:
        for show_id, status in ((1, "current"), (2, "finished"), (3, "current")):
            await con.execute(
                "INSERT INTO kitsu_info (show_id, kitsu_id, show_status) VALUES (?, ?, ?);",
                show_id,
                1000 + show_id,
                status,
            )


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------


async def test_list_shows_returns_page_envelope(client: httpx.AsyncClient, with_statuses: None) -> None:
    result = success(await client.get(f"{API}/shows", params={"filters": ALL_STATUSES}))

    assert set(result) == {"shows", "pagination"}
    assert result["pagination"] == {"page": 1, "limit": 17, "total": 3, "pages": 1}
    assert {show["title"] for show in result["shows"]} == {"Chainsaw Man", "Buddy Daddies", "NieR Automata Ver1.1a"}


async def test_list_shows_without_filters_is_empty(client: httpx.AsyncClient, with_statuses: None) -> None:
    """No status filter means "match nothing", not "match everything".

    The frontend always sends an explicit filter set; this pins down the
    deliberate choice in ShowCollection.filtered_paginated so it cannot be
    "fixed" into returning everything without a failing test.
    """
    result = success(await client.get(f"{API}/shows"))

    assert result["shows"] == []
    assert result["pagination"]["total"] == 0


async def test_list_shows_filters_by_status(client: httpx.AsyncClient, with_statuses: None) -> None:
    result = success(await client.get(f"{API}/shows", params={"filters": "finished"}))

    assert [show["title"] for show in result["shows"]] == ["Buddy Daddies"]
    assert result["pagination"]["total"] == 1


async def test_list_shows_hides_shows_without_metadata(client: httpx.AsyncClient) -> None:
    """Without the with_statuses fixture no show has a kitsu_info row."""
    result = success(await client.get(f"{API}/shows", params={"filters": ALL_STATUSES}))

    assert result["shows"] == []


async def test_list_shows_paginates(client: httpx.AsyncClient, with_statuses: None) -> None:
    params = {"filters": ALL_STATUSES, "limit": 2}
    first = success(await client.get(f"{API}/shows", params={**params, "page": 1}))
    second = success(await client.get(f"{API}/shows", params={**params, "page": 2}))

    assert first["pagination"] == {"page": 1, "limit": 2, "total": 3, "pages": 2}
    assert len(first["shows"]) == 2
    assert len(second["shows"]) == 1

    seen = [show["id_"] for show in first["shows"] + second["shows"]]
    assert len(set(seen)) == 3, "pages overlap"


async def test_list_shows_text_filter(client: httpx.AsyncClient, with_statuses: None) -> None:
    result = success(await client.get(f"{API}/shows", params={"filters": ALL_STATUSES, "text_filter": "chainsaw"}))

    assert [show["title"] for show in result["shows"]] == ["Chainsaw Man"]
    assert result["pagination"]["total"] == 1


async def test_list_shows_text_filter_matches_local_title(client: httpx.AsyncClient, with_statuses: None) -> None:
    result = success(await client.get(f"{API}/shows", params={"filters": ALL_STATUSES, "text_filter": "nier local"}))

    assert [show["title"] for show in result["shows"]] == ["NieR Automata Ver1.1a"]


async def test_list_shows_sort_direction(client: httpx.AsyncClient, with_statuses: None) -> None:
    params = {"filters": ALL_STATUSES, "sort_key": "title"}
    ascending = success(await client.get(f"{API}/shows", params={**params, "sort_direction": "+"}))
    descending = success(await client.get(f"{API}/shows", params={**params, "sort_direction": "-"}))

    ascending_titles = [show["title"] for show in ascending["shows"]]
    assert ascending_titles == sorted(ascending_titles, key=str.lower)
    assert [show["title"] for show in descending["shows"]] == list(reversed(ascending_titles))


@pytest.mark.parametrize("params", [{"page": 0}, {"limit": 0}, {"limit": 101}, {"page": -1}])
async def test_list_shows_rejects_out_of_range_paging(client: httpx.AsyncClient, params: dict) -> None:
    response = await client.get(f"{API}/shows", params=params)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


async def test_get_show(client: httpx.AsyncClient) -> None:
    result = success(await client.get(f"{API}/shows/1"))

    assert result["title"] == "Chainsaw Man"
    assert result["season"] == 1
    assert result["library_id"] == 1
    assert "entries" in result
    assert "webhooks" in result


async def test_get_unknown_show_is_404(client: httpx.AsyncClient) -> None:
    assert error(await client.get(f"{API}/shows/9999"), 404) == "Show with passed ID not found."


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


async def test_create_show(client: httpx.AsyncClient) -> None:
    body = {"title": "Frieren", "library_id": 1, "season": 1, "watch": False}

    result = success(await client.post(f"{API}/shows", json=body), 201)

    assert result["title"] == "Frieren"
    assert result["watch"] is False
    assert result["id_"] > 0


async def test_create_show_persists(client: httpx.AsyncClient, app: MockTsundokuAppState) -> None:
    body = {"title": "Frieren", "library_id": 1, "season": 1, "watch": False}
    created = success(await client.post(f"{API}/shows", json=body), 201)

    async with app.acquire_db() as con:
        title = await con.fetchval("SELECT title FROM shows WHERE id=?;", created["id_"])

    assert title == "Frieren"


async def test_create_show_rejects_invalid_resolution(client: httpx.AsyncClient) -> None:
    body = {"title": "Frieren", "library_id": 1, "season": 1, "watch": False, "preferred_resolution": "42k"}

    assert error(await client.post(f"{API}/shows", json=body), 400) == "Preferred resolution is not a valid resolution."


async def test_create_show_treats_zero_resolution_as_unset(client: httpx.AsyncClient) -> None:
    """The frontend sends "0" for "any resolution"; it must not 400."""
    body = {"title": "Frieren", "library_id": 1, "season": 1, "watch": False, "preferred_resolution": "0"}

    result = success(await client.post(f"{API}/shows", json=body), 201)

    assert result["preferred_resolution"] is None


@pytest.mark.parametrize("body", [{}, {"title": "No Library"}, {"library_id": 1, "season": 1}])
async def test_create_show_rejects_incomplete_body(client: httpx.AsyncClient, body: dict) -> None:
    response = await client.post(f"{API}/shows", json=body)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


async def test_update_show(client: httpx.AsyncClient) -> None:
    body = {"title": "Chainsaw Man", "library_id": 2, "season": 4, "episode_offset": 2, "watch": False}

    result = success(await client.put(f"{API}/shows/1", json=body))

    assert result["library_id"] == 2
    assert result["season"] == 4
    assert result["episode_offset"] == 2
    assert result["watch"] is False


async def test_update_unknown_show_is_404(client: httpx.AsyncClient) -> None:
    body = {"title": "Nope", "library_id": 1}

    assert error(await client.put(f"{API}/shows/9999", json=body), 404) == "Show with passed ID not found."


async def test_update_show_rejects_invalid_resolution(client: httpx.AsyncClient) -> None:
    body = {"title": "Chainsaw Man", "library_id": 1, "preferred_resolution": "nonsense"}

    assert error(await client.put(f"{API}/shows/1", json=body), 400) == "Preferred resolution is not a valid resolution."


async def test_update_show_leaves_omitted_optional_fields_alone(client: httpx.AsyncClient) -> None:
    """season/episode_offset are only applied when explicitly provided."""
    before = success(await client.get(f"{API}/shows/2"))

    result = success(await client.put(f"{API}/shows/2", json={"title": before["title"], "library_id": before["library_id"]}))

    assert result["season"] == before["season"]
    assert result["episode_offset"] == before["episode_offset"]


# ---------------------------------------------------------------------------
# Deletion
# ---------------------------------------------------------------------------


async def test_delete_show(client: httpx.AsyncClient) -> None:
    response = await client.delete(f"{API}/shows/1")

    assert response.status_code == 204
    error(await client.get(f"{API}/shows/1"), 404)


async def test_delete_show_removes_the_row(client: httpx.AsyncClient, app: MockTsundokuAppState) -> None:
    await client.delete(f"{API}/shows/1")

    async with app.acquire_db() as con:
        remaining = await con.fetchval("SELECT COUNT(*) FROM shows WHERE id=1;")

    assert remaining == 0
