"""Fetching .torrent files from hosts that are frequently unreliable."""

import asyncio
from collections.abc import Callable
from typing import Any

import aiohttp
import pytest

from tests.mock import MockResponse, MockTsundokuAppState
from tsundoku.dl_client import Manager
from tsundoku.dl_client.client import TORRENT_FETCH_ATTEMPTS
from tsundoku.dl_client.errors import TorrentFetchError

TORRENT_URL = "https://nyaa.si/download/1234567.torrent"
TORRENT_BODY = b"d8:announce4:test4:infod4:name4:testee"


@pytest.fixture(autouse=True)
def _no_backoff_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the backoff instantly; the delays themselves are not under test."""

    async def instant(_seconds: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", instant)


def failing_then(failures: int, then: Callable[[], MockResponse] | None = None) -> tuple[Callable[[str, dict[str, Any]], MockResponse], list[int]]:
    """A responder that fails ``failures`` times before succeeding."""
    calls: list[int] = []

    def responder(_url: str, _kwargs: dict[str, Any]) -> MockResponse:
        calls.append(1)
        if len(calls) <= failures:
            raise aiohttp.ClientConnectionError("connection reset by peer")
        return then() if then else MockResponse(body=TORRENT_BODY)

    return responder, calls


async def test_succeeds_without_retrying_when_the_host_is_healthy(app: MockTsundokuAppState) -> None:
    responder, calls = failing_then(0)
    app.session.stub("GET", TORRENT_URL, responder)

    assert await app.dl_client.fetch_source(TORRENT_URL) == TORRENT_BODY
    assert len(calls) == 1


async def test_retries_dropped_connections_until_one_lands(app: MockTsundokuAppState) -> None:
    """The exact failure nyaa produces: the connection closes mid-handshake."""
    responder, calls = failing_then(TORRENT_FETCH_ATTEMPTS - 1)
    app.session.stub("GET", TORRENT_URL, responder)

    assert await app.dl_client.fetch_source(TORRENT_URL) == TORRENT_BODY
    assert len(calls) == TORRENT_FETCH_ATTEMPTS


async def test_retries_server_errors(app: MockTsundokuAppState) -> None:
    calls: list[int] = []

    def responder(_url: str, _kwargs: dict[str, Any]) -> MockResponse:
        calls.append(1)
        return MockResponse(status=503) if len(calls) == 1 else MockResponse(body=TORRENT_BODY)

    app.session.stub("GET", TORRENT_URL, responder)

    assert await app.dl_client.fetch_source(TORRENT_URL) == TORRENT_BODY
    assert len(calls) == 2


async def test_gives_up_immediately_on_a_client_error(app: MockTsundokuAppState) -> None:
    """A 404 will not start working, so retrying it only wastes the user's time."""
    calls: list[int] = []

    def responder(_url: str, _kwargs: dict[str, Any]) -> MockResponse:
        calls.append(1)
        return MockResponse(status=404)

    app.session.stub("GET", TORRENT_URL, responder)

    with pytest.raises(TorrentFetchError, match="404"):
        await app.dl_client.fetch_source(TORRENT_URL)

    assert len(calls) == 1


async def test_raises_a_useful_error_once_attempts_are_exhausted(app: MockTsundokuAppState) -> None:
    responder, calls = failing_then(TORRENT_FETCH_ATTEMPTS)
    app.session.stub("GET", TORRENT_URL, responder)

    with pytest.raises(TorrentFetchError, match="temporarily unreachable"):
        await app.dl_client.fetch_source(TORRENT_URL)

    assert len(calls) == TORRENT_FETCH_ATTEMPTS


async def test_an_error_page_is_never_mistaken_for_a_torrent(app: MockTsundokuAppState) -> None:
    """Previously the HTML body was read and handed to bencode, which failed
    with a parse error that said nothing about the real problem."""
    app.session.stub("GET", TORRENT_URL, status=403, body=b"<html>forbidden</html>")

    with pytest.raises(TorrentFetchError, match="HTTP 403"):
        await app.dl_client.fetch_source(TORRENT_URL)


async def test_get_magnet_surfaces_the_fetch_failure(app: MockTsundokuAppState) -> None:
    responder, _ = failing_then(TORRENT_FETCH_ATTEMPTS)
    app.session.stub("GET", TORRENT_URL, responder)

    # MockDownloadManager.get_magnet rejects non-magnet URLs outright, so the
    # real implementation is invoked directly here.
    with pytest.raises(TorrentFetchError):
        await Manager.get_magnet(app.dl_client, TORRENT_URL)
