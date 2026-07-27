import os
from pathlib import Path

import httpx
import pytest

from tests.mock import MockTsundokuAppState

from .envelope import API, error, success

# ---------------------------------------------------------------------------
# API token
# ---------------------------------------------------------------------------


async def test_get_api_token(client: httpx.AsyncClient, app: MockTsundokuAppState) -> None:
    async with app.acquire_db() as con:
        stored = await con.fetchval("SELECT api_key FROM users LIMIT 1;")

    assert success(await client.get(f"{API}/config/token")) == stored


async def test_regenerate_api_token(client: httpx.AsyncClient, app: MockTsundokuAppState) -> None:
    original = success(await client.get(f"{API}/config/token"))

    regenerated = success(await client.post(f"{API}/config/token"))

    assert regenerated != original

    async with app.acquire_db() as con:
        stored = await con.fetchval("SELECT api_key FROM users LIMIT 1;")

    assert stored == regenerated


async def test_regenerating_the_token_revokes_the_old_one(app: MockTsundokuAppState, client: httpx.AsyncClient) -> None:
    """The point of rotation is that the previous key stops working."""
    original = success(await client.get(f"{API}/config/token"))
    success(await client.post(f"{API}/config/token"))

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app.asgi_app),
        base_url="http://testserver",
    ) as keyed:
        response = await keyed.get(f"{API}/libraries", headers={"Authorization": f"Bearer {original}"})

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# General configuration
# ---------------------------------------------------------------------------


async def test_get_general_config(client: httpx.AsyncClient) -> None:
    result = success(await client.get(f"{API}/config/general"))

    assert "host" in result
    assert "port" in result
    assert "locale" in result


async def test_update_general_config(client: httpx.AsyncClient) -> None:
    result = success(await client.patch(f"{API}/config/general", json={"locale": "en", "port": 8080}))

    assert result["locale"] == "en"
    assert result["port"] == 8080

    assert success(await client.get(f"{API}/config/general"))["port"] == 8080


async def test_update_general_config_ignores_omitted_fields(client: httpx.AsyncClient) -> None:
    before = success(await client.get(f"{API}/config/general"))

    result = success(await client.patch(f"{API}/config/general", json={"port": 9999}))

    assert result["port"] == 9999
    assert result["host"] == before["host"]


async def test_empty_general_config_update_is_a_noop(client: httpx.AsyncClient) -> None:
    before = success(await client.get(f"{API}/config/general"))

    assert success(await client.patch(f"{API}/config/general", json={})) == before


@pytest.mark.parametrize(
    ("payload", "fragment"),
    [
        ({"port": 80}, "less than 1024"),
        ({"port": 70000}, "greater than 65535"),
        ({"log_level": "SCREAMING"}, "not a valid log level"),
    ],
)
async def test_update_general_config_validation(client: httpx.AsyncClient, payload: dict, fragment: str) -> None:
    message = error(await client.patch(f"{API}/config/general", json=payload), 400)

    assert fragment in message


async def test_rejected_general_config_is_not_persisted(client: httpx.AsyncClient) -> None:
    before = success(await client.get(f"{API}/config/general"))

    await client.patch(f"{API}/config/general", json={"port": 80})

    assert success(await client.get(f"{API}/config/general"))["port"] == before["port"]


# ---------------------------------------------------------------------------
# Feeds configuration
# ---------------------------------------------------------------------------


async def test_get_feeds_config(client: httpx.AsyncClient) -> None:
    result = success(await client.get(f"{API}/config/feeds"))

    assert "polling_interval" in result
    assert "fuzzy_cutoff" in result


async def test_update_feeds_config(client: httpx.AsyncClient) -> None:
    result = success(await client.patch(f"{API}/config/feeds", json={"polling_interval": 900, "fuzzy_cutoff": 90}))

    assert result["polling_interval"] == 900
    assert result["fuzzy_cutoff"] == 90


@pytest.mark.parametrize(
    ("payload", "fragment"),
    [
        ({"polling_interval": 10}, "at least 180 seconds"),
        ({"complete_check_interval": 1}, "at least 10 seconds"),
        ({"fuzzy_cutoff": 10}, "at least 50%"),
        ({"fuzzy_cutoff": 200}, "at most 100%"),
    ],
)
async def test_update_feeds_config_validation(client: httpx.AsyncClient, payload: dict, fragment: str) -> None:
    message = error(await client.patch(f"{API}/config/feeds", json=payload), 400)

    assert fragment in message


# ---------------------------------------------------------------------------
# Torrent configuration
# ---------------------------------------------------------------------------


async def test_get_torrent_config(client: httpx.AsyncClient) -> None:
    result = success(await client.get(f"{API}/config/torrent"))

    assert "client" in result
    assert "host" in result


async def test_update_torrent_config(client: httpx.AsyncClient) -> None:
    payload = {"client": "deluge", "host": "127.0.0.1", "port": 8112, "secure": False}

    result = success(await client.patch(f"{API}/config/torrent", json=payload))

    assert result["client"] == "deluge"
    assert result["port"] == 8112


async def test_torrent_client_connectivity_test(client: httpx.AsyncClient, app: MockTsundokuAppState) -> None:
    result = success(await client.get(f"{API}/config/torrent/test"))

    assert result == {"success": True, "error": None}
    assert app.flags.DL_CLIENT_CONNECTION_ERROR is False


async def test_torrent_test_is_denied_to_readonly_users(readonly_client: httpx.AsyncClient) -> None:
    """A read-only GET that still mutates a flag must be gated like a write."""
    response = await readonly_client.get(f"{API}/config/torrent/test")

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Directory tree
# ---------------------------------------------------------------------------


def make_dirs(*paths: Path) -> None:
    """Create real directories.

    ``Path.mkdir`` is globally stubbed to a no-op by the ``app`` fixture, which
    keeps the downloader from writing folders during tests. These tests need
    directories that genuinely exist for the endpoint to list, so they go
    through ``os.makedirs`` instead. ``tmp_path`` must also be requested before
    ``client`` so pytest builds it before that stub is installed.
    """
    for path in paths:
        os.makedirs(path, exist_ok=True)  # noqa: PTH103 - Path.mkdir is stubbed out, see above


async def test_tree_lists_subdirectories(tmp_path: Path, client: httpx.AsyncClient) -> None:
    make_dirs(tmp_path / "anime", tmp_path / "movies")
    (tmp_path / "notes.txt").write_text("ignored")

    result = success(await client.post(f"{API}/tree", json={"dir": str(tmp_path)}))

    assert sorted(result["children"]) == ["anime", "movies"], "files should not be listed"
    assert result["current_path"] == str(tmp_path)
    assert result["can_go_back"] is True


async def test_tree_descends_into_a_subdir(tmp_path: Path, client: httpx.AsyncClient) -> None:
    make_dirs(tmp_path / "anime" / "season1")

    result = success(await client.post(f"{API}/tree", json={"dir": str(tmp_path), "subdir": "anime"}))

    assert result["children"] == ["season1"]
    assert result["current_path"] == str(tmp_path / "anime")


async def test_tree_reports_writability(tmp_path: Path, client: httpx.AsyncClient) -> None:
    result = success(await client.post(f"{API}/tree", json={"dir": str(tmp_path)}))

    assert result["root_is_writable"] is True


async def test_tree_at_the_filesystem_root_cannot_go_back(client: httpx.AsyncClient) -> None:
    result = success(await client.post(f"{API}/tree", json={"dir": "/"}))

    assert result["can_go_back"] is False


# ---------------------------------------------------------------------------
# Password change
# ---------------------------------------------------------------------------


async def test_change_password(client: httpx.AsyncClient) -> None:
    body = {"current_password": "password", "new_password": "a-much-longer-password"}

    assert success(await client.post(f"{API}/account/change-password", json=body)) is True


async def attempt_login(app: MockTsundokuAppState, password: str) -> bool:
    """Whether ``password`` authenticates, from a cookie-less client.

    Both outcomes redirect with 302 -- success to "/", failure back to
    "/login" -- so the status code alone proves nothing. The auth cookie is
    the real signal.
    """
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app.asgi_app),
        base_url="http://testserver",
        follow_redirects=False,
    ) as fresh:
        response = await fresh.post("/login", data={"username": "user", "password": password})

    return "tsundoku_auth" in response.cookies


async def test_changed_password_works_for_login(app: MockTsundokuAppState, client: httpx.AsyncClient) -> None:
    assert await attempt_login(app, "password") is True

    body = {"current_password": "password", "new_password": "a-much-longer-password"}
    success(await client.post(f"{API}/account/change-password", json=body))

    assert await attempt_login(app, "a-much-longer-password") is True, "the new password should authenticate"
    assert await attempt_login(app, "password") is False, "the old password should no longer authenticate"


async def test_change_password_rejects_a_wrong_current_password(client: httpx.AsyncClient) -> None:
    body = {"current_password": "not-my-password", "new_password": "a-much-longer-password"}

    assert error(await client.post(f"{API}/account/change-password", json=body), 400) == "Current password is incorrect."


@pytest.mark.parametrize(
    "body",
    [
        {"current_password": "", "new_password": "a-much-longer-password"},
        {"current_password": "password", "new_password": "short"},
        {"current_password": "password"},
        {},
    ],
)
async def test_change_password_rejects_invalid_bodies(client: httpx.AsyncClient, body: dict) -> None:
    assert (await client.post(f"{API}/account/change-password", json=body)).status_code == 422


async def test_change_password_is_denied_to_readonly_users(readonly_client: httpx.AsyncClient) -> None:
    body = {"current_password": "password", "new_password": "a-much-longer-password"}

    assert (await readonly_client.post(f"{API}/account/change-password", json=body)).status_code == 403


# ---------------------------------------------------------------------------
# Misc endpoints
# ---------------------------------------------------------------------------


async def test_check_for_releases(client: httpx.AsyncClient) -> None:
    result = success(await client.get(f"{API}/shows/check"))

    assert isinstance(result, list)


async def test_check_for_releases_is_denied_to_readonly_users(readonly_client: httpx.AsyncClient) -> None:
    assert (await readonly_client.get(f"{API}/shows/check")).status_code == 403


async def test_delete_show_cache(client: httpx.AsyncClient, app: MockTsundokuAppState) -> None:
    async with app.acquire_db() as con:
        await con.execute("INSERT INTO kitsu_info (show_id, kitsu_id, cached_poster_url) VALUES (1, 42, 'https://cdn.test/p.jpg');")

    response = await client.delete(f"{API}/shows/1/cache")
    assert response.status_code == 204

    async with app.acquire_db() as con:
        cached = await con.fetchval("SELECT cached_poster_url FROM kitsu_info WHERE show_id=1;")

    assert cached is None


async def test_webhook_validity_for_unknown_base_is_false(client: httpx.AsyncClient) -> None:
    """A missing webhook reports invalid rather than erroring."""
    assert success(await client.get(f"{API}/webhooks/9999/valid")) is False


async def test_webhook_validity_reflects_the_service_response(client: httpx.AsyncClient, app: MockTsundokuAppState) -> None:
    created = success(
        await client.post(
            f"{API}/webhooks",
            json={
                "name": "notify",
                "service": "discord",
                "url": "https://discord.test/hook",
                "content_fmt": "{name}",
                "default_triggers": "",
            },
        ),
        201,
    )

    app.session.stub("HEAD", "https://discord.test", status=200)
    assert success(await client.get(f"{API}/webhooks/{created['base_id']}/valid")) is True

    app.session.stub("HEAD", "https://discord.test", status=404)
    assert success(await client.get(f"{API}/webhooks/{created['base_id']}/valid")) is False
