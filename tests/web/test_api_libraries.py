import httpx
import pytest

from tests.mock import MockTsundokuAppState

from .envelope import API, error, success


async def test_list_libraries(client: httpx.AsyncClient) -> None:
    result = success(await client.get(f"{API}/libraries"))

    assert [library["folder"] for library in result] == ["anime1", "anime2"]
    assert [library["is_default"] for library in result] == [True, False]


async def test_get_library_by_id(client: httpx.AsyncClient) -> None:
    result = success(await client.get(f"{API}/libraries/1"))

    # This endpoint declares Success[list[Library]], so a single library still
    # comes back wrapped in a list.
    assert result == [{"id_": 1, "folder": "anime1", "is_default": True}]


async def test_get_unknown_library_is_404(client: httpx.AsyncClient) -> None:
    message = error(await client.get(f"{API}/libraries/9999"), 404)

    assert message == "Library with specified ID does not exist."


async def test_create_library(client: httpx.AsyncClient) -> None:
    result = success(await client.post(f"{API}/libraries", json={"folder": "/anime/new"}), 201)

    assert result["folder"] == "/anime/new"
    assert result["is_default"] is False

    listed = success(await client.get(f"{API}/libraries"))
    assert "/anime/new" in [library["folder"] for library in listed]


async def test_update_library_folder(client: httpx.AsyncClient) -> None:
    created = success(await client.post(f"{API}/libraries", json={"folder": "/anime/old"}), 201)

    result = success(
        await client.put(
            f"{API}/libraries/{created['id_']}",
            json={"folder": "/anime/moved", "is_default": False},
        )
    )

    assert result["folder"] == "/anime/moved"
    assert result["id_"] == created["id_"]


async def test_update_library_can_promote_to_default(client: httpx.AsyncClient) -> None:
    """Promoting a library must demote the previous default, not add a second."""
    created = success(await client.post(f"{API}/libraries", json={"folder": "/anime/new"}), 201)

    success(
        await client.put(
            f"{API}/libraries/{created['id_']}",
            json={"folder": "/anime/new", "is_default": True},
        )
    )

    listed = success(await client.get(f"{API}/libraries"))
    defaults = [library["id_"] for library in listed if library["is_default"]]
    assert defaults == [created["id_"]]


async def test_update_unknown_library_is_404(client: httpx.AsyncClient) -> None:
    response = await client.put(f"{API}/libraries/9999", json={"folder": "/x", "is_default": False})

    assert error(response, 404) == "Library with specified ID does not exist."


async def test_delete_library(client: httpx.AsyncClient) -> None:
    created = success(await client.post(f"{API}/libraries", json={"folder": "/anime/temp"}), 201)

    response = await client.delete(f"{API}/libraries/{created['id_']}")
    assert response.status_code == 204
    assert not response.content

    error(await client.get(f"{API}/libraries/{created['id_']}"), 404)


async def test_delete_unknown_library_is_404(client: httpx.AsyncClient) -> None:
    assert error(await client.delete(f"{API}/libraries/9999"), 404) == "Library with specified ID does not exist."


@pytest.mark.parametrize("payload", [{}, {"folder": None}, {"fldr": "/anime"}])
async def test_create_library_rejects_malformed_body(client: httpx.AsyncClient, payload: dict) -> None:
    response = await client.post(f"{API}/libraries", json=payload)

    assert response.status_code == 422


async def test_library_changes_persist_to_the_database(client: httpx.AsyncClient, app: MockTsundokuAppState) -> None:
    """Guard against an endpoint that only mutates its in-memory model."""
    created = success(await client.post(f"{API}/libraries", json={"folder": "/anime/persisted"}), 201)

    async with app.acquire_db() as con:
        folder = await con.fetchval("SELECT folder FROM library WHERE id=?;", created["id_"])

    assert folder == "/anime/persisted"
