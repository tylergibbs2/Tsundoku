from pathlib import Path
from typing import Any, cast

import aiohttp
import pytest

from tests.mock import MockClientSession, MockResponse
from tsundoku.dl_client.deluge.client import DelugeClient

URL = "http://deluge.test:8112/json"


def make_client(session: MockClientSession, **overrides: Any) -> DelugeClient:
    kwargs: dict[str, Any] = {"host": "deluge.test", "port": 8112, "secure": False, "auth": "hunter2"}
    kwargs.update(overrides)
    return DelugeClient(cast("aiohttp.ClientSession", session), **kwargs)


def stub_rpc(session: MockClientSession, results: dict[str, Any], *, authed: bool = True) -> None:
    """Route Deluge's JSON-RPC calls by method name.

    Deluge POSTs every call to the same ``/json`` endpoint, so the only way to
    tell ``auth.login`` from ``webapi.get_torrents`` is the request body.
    """

    def responder(_url: str, kwargs: dict[str, Any]) -> MockResponse:
        method = kwargs["json"]["method"]
        if method == "auth.check_session":
            return MockResponse(json={"result": authed})
        if method in results:
            return MockResponse(json=results[method])
        raise AssertionError(f"unexpected Deluge RPC method: {method}")

    session.stub("POST", URL, responder)


@pytest.fixture(name="session")
def session_fixture() -> MockClientSession:
    return MockClientSession()


@pytest.fixture(name="client")
def client_fixture(session: MockClientSession) -> DelugeClient:
    return make_client(session)


# ---------------------------------------------------------------------------
# URL building
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("secure", "expected"),
    [(False, "http://deluge.test:8112/json"), (True, "https://deluge.test:8112/json")],
)
def test_build_api_url(session: MockClientSession, secure: bool, expected: str) -> None:
    client = make_client(session, secure=secure)
    assert client.url == expected


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


async def test_login_uses_existing_session(client: DelugeClient, session: MockClientSession) -> None:
    """A live session short-circuits before auth.login is ever sent."""
    stub_rpc(session, {}, authed=True)

    result = await client.login()

    assert result.success
    assert result.error is None
    sent = [r.json["method"] for r in session.requests_for("POST", URL)]
    assert sent == ["auth.check_session"]


async def test_login_falls_back_to_password(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(session, {"auth.login": {"result": True}}, authed=False)

    result = await client.login()

    assert result.success
    sent = session.requests_for("POST", URL)
    assert [r.json["method"] for r in sent] == ["auth.check_session", "auth.login"]
    assert sent[1].json["params"] == ["hunter2"]


async def test_login_rejects_bad_password(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(session, {"auth.login": {"result": False}}, authed=False)

    result = await client.login()

    assert not result.success
    assert result.error == "Deluge rejected the configured password."


async def test_login_surfaces_server_error_message(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(session, {"auth.login": {"error": {"message": "Password is required."}}}, authed=False)

    result = await client.login()

    assert not result.success
    assert result.error == "Password is required."


async def test_login_reports_connection_failure(client: DelugeClient, session: MockClientSession) -> None:
    def unreachable(_url: str, _kwargs: dict[str, Any]) -> MockResponse:
        raise aiohttp.ClientConnectionError("connection closed")

    session.stub("POST", URL, unreachable)

    result = await client.login()

    assert not result.success
    assert result.error is not None
    assert "Connection to Deluge at" in result.error


async def test_test_client_delegates_to_login(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(session, {}, authed=True)
    assert (await client.test_client()).success


async def test_request_counter_increments_per_call(client: DelugeClient, session: MockClientSession) -> None:
    """Deluge JSON-RPC ids must be distinct within a session."""
    stub_rpc(session, {"webapi.get_torrents": {"result": {"torrents": []}}}, authed=True)

    await client.check_torrent_ratio("abc")

    ids = [r.json["id"] for r in session.requests_for("POST", URL)]
    assert len(ids) == len(set(ids)), f"duplicate JSON-RPC ids: {ids}"


# ---------------------------------------------------------------------------
# Torrent state
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("state", "expected"),
    [("Seeding", True), ("Downloading", False), ("Paused", False), ("Error", False)],
)
async def test_check_torrent_completed(client: DelugeClient, session: MockClientSession, state: str, expected: bool) -> None:
    stub_rpc(session, {"webapi.get_torrents": {"result": {"torrents": [{"state": state}]}}})

    assert await client.check_torrent_completed("abc") is expected


async def test_check_torrent_completed_missing_torrent(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(session, {"webapi.get_torrents": {"result": {"torrents": []}}})

    assert await client.check_torrent_completed("abc") is False


async def test_check_torrent_ratio(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(session, {"webapi.get_torrents": {"result": {"torrents": [{"ratio": 1.75}]}}})

    assert await client.check_torrent_ratio("abc") == 1.75


async def test_check_torrent_ratio_absent_field(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(session, {"webapi.get_torrents": {"result": {"torrents": [{"state": "Seeding"}]}}})

    assert await client.check_torrent_ratio("abc") is None


async def test_check_torrent_ratio_missing_torrent(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(session, {"webapi.get_torrents": {"result": {"torrents": []}}})

    assert await client.check_torrent_ratio("abc") is None


async def test_get_torrent_fp_joins_path(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(
        session,
        {"webapi.get_torrents": {"result": {"torrents": [{"name": "ep01.mkv", "move_completed_path": "/downloads/done"}]}}},
    )

    assert await client.get_torrent_fp("abc") == Path("/downloads/done/ep01.mkv")


async def test_get_torrent_fp_missing_torrent(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(session, {"webapi.get_torrents": {"result": {"torrents": []}}})

    assert await client.get_torrent_fp("abc") is None


async def test_check_torrent_exists(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(
        session,
        {"webapi.get_torrents": {"result": {"torrents": [{"name": "ep01.mkv", "move_completed_path": "/downloads"}]}}},
    )

    assert await client.check_torrent_exists("abc") is True


async def test_check_torrent_exists_missing(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(session, {"webapi.get_torrents": {"result": {"torrents": []}}})

    assert await client.check_torrent_exists("abc") is False


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


async def test_add_torrent_returns_hash(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(session, {"webapi.add_torrent": {"result": "deadbeef"}})

    assert await client.add_torrent("magnet:?xt=urn:btih:deadbeef") == "deadbeef"

    add = [r for r in session.requests_for("POST", URL) if r.json["method"] == "webapi.add_torrent"]
    assert add[0].json["params"] == ["magnet:?xt=urn:btih:deadbeef"]


async def test_delete_torrent_forwards_with_files_flag(client: DelugeClient, session: MockClientSession) -> None:
    stub_rpc(session, {"webapi.remove_torrent": {"result": True}})

    await client.delete_torrent("abc", with_files=False)

    remove = [r for r in session.requests_for("POST", URL) if r.json["method"] == "webapi.remove_torrent"]
    assert remove[0].json["params"] == ["abc", False]
