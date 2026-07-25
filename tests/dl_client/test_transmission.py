import asyncio
import base64
from pathlib import Path
from typing import Any

import aiohttp
import pytest

from tests.mock import MockClientSession, MockResponse
from tsundoku.dl_client.abstract import TestClientResult as ClientResult  # aliased: a Test* name would trip pytest collection
from tsundoku.dl_client.transmission.client import TransmissionClient

BASE = "http://tm.test:9091"
RPC_URL = f"{BASE}/transmission/rpc"


def make_client(session: MockClientSession, **overrides: Any) -> TransmissionClient:
    kwargs: dict[str, Any] = {
        "host": "tm.test",
        "port": 9091,
        "secure": False,
        "auth": {"username": "user", "password": "pass"},
    }
    kwargs.update(overrides)
    return TransmissionClient(session, **kwargs)


def sequence(session: MockClientSession, *responses: MockResponse) -> None:
    """Serve ``responses`` in order, repeating the last one once exhausted.

    Transmission's 409 handshake means a single call can legitimately hit the
    same URL twice with different results, which a static stub cannot express.
    """
    remaining = list(responses)

    def responder(_url: str, _kwargs: dict[str, Any]) -> MockResponse:
        return remaining.pop(0) if len(remaining) > 1 else remaining[0]

    session.stub("POST", RPC_URL, responder)


def ok(payload: dict[str, Any]) -> MockResponse:
    return MockResponse(status=200, json=payload)


@pytest.fixture(name="session")
def session_fixture() -> MockClientSession:
    return MockClientSession()


@pytest.fixture(name="client")
def client_fixture(session: MockClientSession) -> TransmissionClient:
    return make_client(session)


@pytest.fixture(name="no_sleep")
def no_sleep_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _instant(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", _instant)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("secure", "expected"),
    [(False, "http://tm.test:9091"), (True, "https://tm.test:9091")],
)
def test_build_api_url(session: MockClientSession, secure: bool, expected: str) -> None:
    assert make_client(session, secure=secure).url == expected


def test_credentials_are_basic_auth_encoded(client: TransmissionClient) -> None:
    assert base64.b64decode(client.credentials).decode() == "user:pass"


def test_missing_auth_encodes_empty_credentials(session: MockClientSession) -> None:
    client = make_client(session, auth={})
    assert base64.b64decode(client.credentials).decode() == ":"


# ---------------------------------------------------------------------------
# test_client / session handshake
# ---------------------------------------------------------------------------


async def test_test_client_success(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, ok({"result": "success"}))

    result = await client.test_client()

    assert result.success
    sent = session.requests_for("POST", RPC_URL)[0]
    assert sent.json == {"method": "session-stats", "arguments": {}}
    assert sent.headers["Authorization"] == f"Basic {client.credentials}"


async def test_test_client_performs_409_handshake(client: TransmissionClient, session: MockClientSession) -> None:
    """A 409 carries the session id Transmission expects on the retry."""
    sequence(
        session,
        MockResponse(status=409, headers={"X-Transmission-Session-Id": "session-abc"}),
        ok({"result": "success"}),
    )

    assert (await client.test_client()).success
    assert client.session_id == "session-abc"

    retry = session.requests_for("POST", RPC_URL)[1]
    assert retry.headers["X-Transmission-Session-Id"] == "session-abc"


async def test_test_client_gives_up_after_repeated_409(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, MockResponse(status=409, headers={"X-Transmission-Session-Id": "x"}))

    result = await client.test_client()

    assert not result.success
    assert result.error is not None
    assert "valid session" in result.error
    assert len(session.requests_for("POST", RPC_URL)) == 2


@pytest.mark.parametrize(
    ("status", "fragment"),
    [
        (401, "rejected the configured username or password"),
        (500, "unexpected status 500"),
    ],
)
async def test_test_client_failure_messages(client: TransmissionClient, session: MockClientSession, status: int, fragment: str) -> None:
    sequence(session, MockResponse(status=status))

    result = await client.test_client()

    assert not result.success
    assert result.error is not None
    assert fragment in result.error


async def test_test_client_reports_rpc_level_error(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, ok({"result": "method not allowed"}))

    result = await client.test_client()

    assert not result.success
    assert result.error is not None
    assert "method not allowed" in result.error


async def test_test_client_reports_connection_failure(client: TransmissionClient, session: MockClientSession) -> None:
    def unreachable(_url: str, _kwargs: dict[str, Any]) -> MockResponse:
        raise aiohttp.ClientConnectionError("refused")

    session.stub("POST", RPC_URL, unreachable)

    result = await client.test_client()

    assert not result.success
    assert result.error is not None
    assert "Connection to Transmission at" in result.error


# ---------------------------------------------------------------------------
# request() transport behaviour
# ---------------------------------------------------------------------------


async def test_request_retries_on_409_with_new_session_id(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(
        session,
        MockResponse(status=409, headers={"X-Transmission-Session-Id": "fresh"}),
        ok({"result": "success", "arguments": {"torrents": []}}),
    )

    result = await client.request("torrent-get")

    assert result["result"] == "success"
    assert client.session_id == "fresh"


async def test_request_retries_bad_request(client: TransmissionClient, session: MockClientSession, no_sleep: None) -> None:
    sequence(session, MockResponse(status=400))

    assert await client.request("torrent-get") == {}
    assert len(session.requests_for("POST", RPC_URL)) == 5


async def test_request_gives_up_on_unexpected_status(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, MockResponse(status=500))

    assert await client.request("torrent-get") == {}
    assert len(session.requests_for("POST", RPC_URL)) == 1


# ---------------------------------------------------------------------------
# Torrent state
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "finished", "expected"),
    [
        (0, True, True),  # stopped after finishing
        (0, False, False),  # stopped mid-download
        (5, False, True),  # seeding
        (6, False, True),  # seeding
        (4, False, False),  # downloading
    ],
)
async def test_check_torrent_completed(client: TransmissionClient, session: MockClientSession, status: int, finished: bool, expected: bool) -> None:
    sequence(session, ok({"result": "success", "arguments": {"torrents": [{"status": status, "isFinished": finished}]}}))

    assert await client.check_torrent_completed("abc") is expected


async def test_check_torrent_completed_missing_torrent(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, ok({"result": "success", "arguments": {"torrents": []}}))

    assert await client.check_torrent_completed("abc") is False


async def test_check_torrent_completed_on_rpc_error(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, ok({"result": "failure"}))

    assert await client.check_torrent_completed("abc") is False


async def test_check_torrent_ratio(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, ok({"result": "success", "arguments": {"torrents": [{"uploadRatio": 3.25}]}}))

    assert await client.check_torrent_ratio("abc") == 3.25


async def test_check_torrent_ratio_absent_field(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, ok({"result": "success", "arguments": {"torrents": [{"status": 5}]}}))

    assert await client.check_torrent_ratio("abc") is None


async def test_check_torrent_ratio_missing_torrent(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, ok({"result": "success", "arguments": {"torrents": []}}))

    assert await client.check_torrent_ratio("abc") is None


async def test_get_torrent_fp(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, ok({"result": "success", "arguments": {"torrents": [{"downloadDir": "/downloads", "name": "ep01.mkv"}]}}))

    assert await client.get_torrent_fp("abc") == Path("/downloads/ep01.mkv")


async def test_get_torrent_fp_missing_torrent(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, ok({"result": "success", "arguments": {"torrents": []}}))

    assert await client.get_torrent_fp("abc") is None


async def test_check_torrent_exists(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, ok({"result": "success", "arguments": {"torrents": [{"downloadDir": "/d", "name": "ep01.mkv"}]}}))

    assert await client.check_torrent_exists("abc") is True


async def test_check_torrent_exists_missing(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, ok({"result": "success", "arguments": {"torrents": []}}))

    assert await client.check_torrent_exists("abc") is False


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


async def test_add_torrent_returns_hash(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, ok({"result": "success", "arguments": {"torrent-added": {"hashString": "deadbeef"}}}))

    assert await client.add_torrent("magnet:?xt=urn:btih:deadbeef") == "deadbeef"

    sent = session.requests_for("POST", RPC_URL)[0]
    assert sent.json == {"method": "torrent-add", "arguments": {"filename": "magnet:?xt=urn:btih:deadbeef"}}


async def test_add_torrent_on_rpc_error(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, ok({"result": "duplicate torrent"}))

    assert await client.add_torrent("magnet:?xt=urn:btih:deadbeef") is None


@pytest.mark.parametrize("with_files", [True, False])
async def test_delete_torrent_forwards_flag(client: TransmissionClient, session: MockClientSession, with_files: bool) -> None:
    sequence(session, ok({"result": "success"}))

    await client.delete_torrent("abc", with_files=with_files)

    sent = session.requests_for("POST", RPC_URL)[0]
    assert sent.json == {
        "method": "torrent-remove",
        "arguments": {"ids": ["abc"], "delete-local-data": with_files},
    }


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------


async def test_login_succeeds_via_session_handshake(client: TransmissionClient, session: MockClientSession) -> None:
    """Transmission has no login endpoint, so login proves out the credentials."""
    sequence(session, ok({"result": "success"}))

    result = await client.login()

    assert isinstance(result, ClientResult)
    assert result.success
    assert result.error is None


async def test_login_reports_bad_credentials(client: TransmissionClient, session: MockClientSession) -> None:
    sequence(session, MockResponse(status=401))

    result = await client.login()

    assert isinstance(result, ClientResult)
    assert not result.success
    assert result.error is not None
    assert "rejected the configured username or password" in result.error


async def test_login_satisfies_the_abstract_contract(client: TransmissionClient, session: MockClientSession) -> None:
    """Regression guard: login used to delegate to the abstract method, which
    has only a docstring for a body and therefore returned None."""
    sequence(session, ok({"result": "success"}))

    annotation = TransmissionClient.login.__annotations__["return"]
    assert isinstance(await client.login(), annotation)
