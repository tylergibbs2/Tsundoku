import httpx
import pytest_asyncio

from tests.mock import MockTsundokuAppState

from .envelope import API, error, success


@pytest_asyncio.fixture(name="entry_id")
async def entry_id_fixture(app: MockTsundokuAppState) -> int:
    async with app.acquire_db() as con:
        return await con.fetchval(
            """
            INSERT INTO show_entry (show_id, episode, current_state, torrent_hash)
            VALUES (1, 4, 'completed', 'abc123')
            RETURNING id;
            """
        )


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


async def test_get_entry(client: httpx.AsyncClient, entry_id: int) -> None:
    result = success(await client.get(f"{API}/entries/{entry_id}"))

    assert result["episode"] == 4
    assert result["show_id"] == 1
    assert result["state"] == "completed"


async def test_get_unknown_entry_is_404(client: httpx.AsyncClient) -> None:
    assert error(await client.get(f"{API}/entries/9999"), 404) == "Entry with specified ID does not exist."


async def test_list_show_entries(client: httpx.AsyncClient, entry_id: int) -> None:
    result = success(await client.get(f"{API}/shows/1/entries"))

    assert [entry["id"] for entry in result] == [entry_id]
    assert result[0]["episode"] == 4


async def test_list_show_entries_is_scoped_to_the_show(client: httpx.AsyncClient, entry_id: int) -> None:
    assert success(await client.get(f"{API}/shows/2/entries")) == []


async def test_get_show_entry(client: httpx.AsyncClient, entry_id: int) -> None:
    result = success(await client.get(f"{API}/shows/1/entries/{entry_id}"))

    assert result["id"] == entry_id
    assert result["episode"] == 4


async def test_get_unknown_show_entry_is_404(client: httpx.AsyncClient) -> None:
    response = await client.get(f"{API}/shows/1/entries/9999")

    assert error(response, 404) == "Entry with specified ID does not exist."


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


async def test_create_entry_from_object_body(client: httpx.AsyncClient) -> None:
    result = success(await client.post(f"{API}/shows/1/entries", json={"episode": 7}), 201)

    assert result["episode"] == 7
    assert result["state"] == "completed"
    assert result["created_manually"] is True


async def test_create_entries_from_array_body(client: httpx.AsyncClient) -> None:
    """The endpoint accepts either a single object or a list of them."""
    body = [{"episode": 8}, {"episode": 9}]

    result = success(await client.post(f"{API}/shows/1/entries", json=body), 201)

    assert [entry["episode"] for entry in result] == [8, 9]


async def test_created_entry_is_listed(client: httpx.AsyncClient) -> None:
    created = success(await client.post(f"{API}/shows/1/entries", json={"episode": 7}), 201)

    listed = success(await client.get(f"{API}/shows/1/entries"))

    assert created["id"] in [entry["id"] for entry in listed]


async def test_create_entry_rejects_missing_episode(client: httpx.AsyncClient) -> None:
    response = await client.post(f"{API}/shows/1/entries", json={"magnet": "magnet:?xt=urn:btih:abc"})

    assert response.status_code == 400


async def test_create_entry_rejects_scalar_body(client: httpx.AsyncClient) -> None:
    response = await client.post(f"{API}/shows/1/entries", json="not-a-body")

    assert error(response, 400) == "Invalid request body."


# ---------------------------------------------------------------------------
# Deletion
# ---------------------------------------------------------------------------


async def test_delete_entry(client: httpx.AsyncClient, entry_id: int) -> None:
    response = await client.delete(f"{API}/shows/1/entries/{entry_id}")

    assert response.status_code == 204
    assert success(await client.get(f"{API}/shows/1/entries")) == []


async def test_delete_entry_removes_the_row(client: httpx.AsyncClient, app: MockTsundokuAppState, entry_id: int) -> None:
    await client.delete(f"{API}/shows/1/entries/{entry_id}")

    async with app.acquire_db() as con:
        remaining = await con.fetchval("SELECT COUNT(*) FROM show_entry WHERE id=?;", entry_id)

    assert remaining == 0
