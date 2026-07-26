import asyncio
from pathlib import Path
from typing import Any, cast

import aiohttp
import pytest

from tests.mock import MockClientSession, MockResponse
from tsundoku.dl_client.qbittorrent.client import qBittorrentClient

BASE = "http://qb.test:8080"
LOGIN_URL = f"{BASE}/api/v2/auth/login"
INFO_URL = f"{BASE}/api/v2/torrents/info"
JSON_HEADERS = {"Content-Type": "application/json"}


def make_client(session: MockClientSession, **overrides: Any) -> qBittorrentClient:
    kwargs: dict[str, Any] = {"host": "qb.test", "port": 8080, "secure": False}
    kwargs.update(overrides)
    auth = kwargs.pop("auth", {"username": "admin", "password": "adminadmin"})
    return qBittorrentClient(cast("aiohttp.ClientSession", session), auth, **kwargs)


@pytest.fixture(name="session")
def session_fixture() -> MockClientSession:
    return MockClientSession()


@pytest.fixture(name="client")
def client_fixture(session: MockClientSession) -> qBittorrentClient:
    return make_client(session)


@pytest.fixture(name="authed_client")
def authed_client_fixture(session: MockClientSession, client: qBittorrentClient) -> qBittorrentClient:
    session.stub("POST", LOGIN_URL, status=200, text="Ok.")
    return client


@pytest.fixture(name="no_sleep")
def no_sleep_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    """Collapse the client's backoff so retry paths stay fast to exercise."""

    async def _instant(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", _instant)


# ---------------------------------------------------------------------------
# URL building
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("secure", "expected"),
    [(False, "http://qb.test:8080"), (True, "https://qb.test:8080")],
)
def test_build_api_url(session: MockClientSession, secure: bool, expected: str) -> None:
    assert make_client(session, secure=secure).url == expected


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


async def test_login_legacy_ok_body(client: qBittorrentClient, session: MockClientSession) -> None:
    """qBittorrent < 5.2.0 answers 200 with a literal "Ok." body."""
    session.stub("POST", LOGIN_URL, status=200, text="Ok.")

    result = await client.login()

    assert result.success
    sent = session.requests_for("POST", LOGIN_URL)[0]
    assert sent.kwargs["data"] == {"username": "admin", "password": "adminadmin"}
    assert sent.headers["Referer"] == BASE


async def test_login_accepts_no_content(client: qBittorrentClient, session: MockClientSession) -> None:
    """qBittorrent >= 5.2.0 answers 204 and sets the cookie via header."""
    session.stub("POST", LOGIN_URL, status=204)

    assert (await client.login()).success


async def test_login_tolerates_body_whitespace_and_case(client: qBittorrentClient, session: MockClientSession) -> None:
    session.stub("POST", LOGIN_URL, status=200, text="  OK.\n")

    assert (await client.login()).success


async def test_login_is_cached_per_credentials(client: qBittorrentClient, session: MockClientSession) -> None:
    session.stub("POST", LOGIN_URL, status=200, text="Ok.")

    assert (await client.login()).success
    assert (await client.login()).success

    assert len(session.requests_for("POST", LOGIN_URL)) == 1, "second login should hit the cache"


@pytest.mark.parametrize(
    ("status", "fragment"),
    [
        (403, "temporarily banned"),
        (401, "rejected the configured username or password"),
        (200, "rejected the configured username or password"),
        (500, "unexpected status 500"),
    ],
)
async def test_login_failure_messages(client: qBittorrentClient, session: MockClientSession, status: int, fragment: str) -> None:
    # A 200 with any body other than "Ok." is a rejection, not a success.
    session.stub("POST", LOGIN_URL, status=status, text="Fails.")

    result = await client.login()

    assert not result.success
    assert result.error is not None
    assert fragment in result.error


async def test_failed_login_is_not_cached(client: qBittorrentClient, session: MockClientSession) -> None:
    session.stub("POST", LOGIN_URL, status=401, text="Fails.")

    await client.login()
    await client.login()

    assert len(session.requests_for("POST", LOGIN_URL)) == 2


async def test_login_reports_connection_failure(client: qBittorrentClient, session: MockClientSession) -> None:
    def unreachable(_url: str, _kwargs: dict[str, Any]) -> MockResponse:
        raise aiohttp.ClientConnectionError("refused")

    session.stub("POST", LOGIN_URL, unreachable)

    result = await client.login()

    assert not result.success
    assert result.error is not None
    assert "Connection to qBittorrent at" in result.error


# ---------------------------------------------------------------------------
# request() transport behaviour
# ---------------------------------------------------------------------------


async def test_request_parses_json_only_with_content_type(authed_client: qBittorrentClient, session: MockClientSession) -> None:
    """Without a JSON content type the body is handed back as raw text."""
    session.stub("GET", INFO_URL, status=200, text='[{"hash": "abc"}]')

    assert await authed_client.request("get", "torrents", "info") == '[{"hash": "abc"}]'

    session.stub("GET", INFO_URL, status=200, json=[{"hash": "abc"}], headers=JSON_HEADERS)

    assert await authed_client.request("get", "torrents", "info") == [{"hash": "abc"}]


async def test_request_reauthenticates_on_forbidden(authed_client: qBittorrentClient, session: MockClientSession) -> None:
    session.stub("GET", INFO_URL, status=403)

    assert await authed_client.request("get", "torrents", "info") == {}
    # Five attempts, each followed by a re-login. The first login is the
    # fixture's own, and the cache is cleared by each 403 re-auth.
    assert len(session.requests_for("GET", INFO_URL)) == 5


async def test_request_retries_bad_request(authed_client: qBittorrentClient, session: MockClientSession, no_sleep: None) -> None:
    session.stub("GET", INFO_URL, status=400)

    assert await authed_client.request("get", "torrents", "info") == {}
    assert len(session.requests_for("GET", INFO_URL)) == 5


async def test_request_gives_up_on_unexpected_status(authed_client: qBittorrentClient, session: MockClientSession) -> None:
    session.stub("GET", INFO_URL, status=500)

    assert await authed_client.request("get", "torrents", "info") == {}
    assert len(session.requests_for("GET", INFO_URL)) == 1, "5xx should not be retried"


# ---------------------------------------------------------------------------
# Torrent state
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("uploading", True),
        ("stalledUP", True),
        ("pausedUP", True),
        ("forcedUP", True),
        ("queuedUP", True),
        ("checkingUP", True),
        ("completed", True),
        ("downloading", False),
        ("stalledDL", False),
        ("error", False),
    ],
)
async def test_check_torrent_completed(authed_client: qBittorrentClient, session: MockClientSession, state: str, expected: bool) -> None:
    session.stub("GET", INFO_URL, json=[{"state": state}], headers=JSON_HEADERS)

    assert await authed_client.check_torrent_completed("abc") is expected


async def test_check_torrent_completed_missing_torrent(authed_client: qBittorrentClient, session: MockClientSession) -> None:
    session.stub("GET", INFO_URL, json=[], headers=JSON_HEADERS)

    assert await authed_client.check_torrent_completed("abc") is False


async def test_check_torrent_ratio(authed_client: qBittorrentClient, session: MockClientSession) -> None:
    session.stub("GET", INFO_URL, json=[{"state": "uploading", "ratio": 2.5}], headers=JSON_HEADERS)

    assert await authed_client.check_torrent_ratio("abc") == 2.5


async def test_check_torrent_ratio_missing_torrent(authed_client: qBittorrentClient, session: MockClientSession) -> None:
    session.stub("GET", INFO_URL, json=[], headers=JSON_HEADERS)

    assert await authed_client.check_torrent_ratio("abc") is None


async def test_get_torrent_fp(authed_client: qBittorrentClient, session: MockClientSession) -> None:
    session.stub("GET", INFO_URL, json=[{"hash": "abc", "content_path": "/downloads/ep01.mkv"}], headers=JSON_HEADERS)

    assert await authed_client.get_torrent_fp("abc") == Path("/downloads/ep01.mkv")


async def test_get_torrent_fp_rejects_hash_mismatch(authed_client: qBittorrentClient, session: MockClientSession) -> None:
    """qBittorrent filters server-side; a mismatch means we got someone else's torrent."""
    session.stub("GET", INFO_URL, json=[{"hash": "different", "content_path": "/downloads/ep01.mkv"}], headers=JSON_HEADERS)

    assert await authed_client.get_torrent_fp("abc") is None


async def test_get_torrent_fp_missing_torrent(authed_client: qBittorrentClient, session: MockClientSession) -> None:
    session.stub("GET", INFO_URL, json=[], headers=JSON_HEADERS)

    assert await authed_client.get_torrent_fp("abc") is None


async def test_check_torrent_exists(authed_client: qBittorrentClient, session: MockClientSession) -> None:
    session.stub("GET", INFO_URL, json=[{"hash": "abc", "content_path": "/downloads/ep01.mkv"}], headers=JSON_HEADERS)

    assert await authed_client.check_torrent_exists("abc") is True


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------


async def test_add_torrent_extracts_lowercased_hash(authed_client: qBittorrentClient, session: MockClientSession) -> None:
    magnet = "magnet:?xt=urn:btih:ABCDEF0123456789&dn=show"
    session.stub("POST", f"{BASE}/api/v2/torrents/add", status=200)

    assert await authed_client.add_torrent(magnet) == "abcdef0123456789"

    sent = session.requests_for("POST", f"{BASE}/api/v2/torrents/add")[0]
    assert sent.kwargs["data"] == {"urls": magnet}


async def test_add_torrent_without_hash_returns_none(authed_client: qBittorrentClient, session: MockClientSession) -> None:
    session.stub("POST", f"{BASE}/api/v2/torrents/add", status=200)

    assert await authed_client.add_torrent("magnet:?xt=urn:nothing") is None


@pytest.mark.parametrize(("with_files", "expected"), [(True, "true"), (False, "false")])
async def test_delete_torrent_forwards_flag(authed_client: qBittorrentClient, session: MockClientSession, with_files: bool, expected: str) -> None:
    delete_url = f"{BASE}/api/v2/torrents/delete"
    session.stub("GET", delete_url, status=200)

    await authed_client.delete_torrent("abc", with_files=with_files)

    sent = session.requests_for("GET", delete_url)[0]
    assert sent.params == {"hashes": "abc", "deleteFiles": expected}
