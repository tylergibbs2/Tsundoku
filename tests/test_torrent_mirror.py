"""The development-only mirror that swaps real torrents for local synthetic ones."""

import hashlib
import logging
from typing import Any

import bencodepy
import pytest

from tests.mock import MockTsundokuAppState
from tsundoku.dl_client import Manager

REAL_MAGNET = "magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567&dn=Some+Release.mkv&tr=http%3A%2F%2Ftracker.example%2Fannounce"
REAL_TORRENT_URL = "https://nyaa.si/download/1234567.torrent"
MIRROR = "http://localhost:8081"


def make_torrent(name: bytes, length: int = 1024) -> bytes:
    info = {b"name": name, b"length": length, b"piece length": 32768, b"pieces": b"\0" * 20}
    return bencodepy.encode({b"announce": b"http://tracker:6969/announce", b"info": info})


REAL_BYTES = make_torrent(b"Real.Release.mkv")
SYNTHETIC_BYTES = make_torrent(b"Real.Release.mkv", length=2048)


def use_mirror(app: MockTsundokuAppState, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app.flags, "TORRENT_MIRROR_URL", MIRROR)


async def test_torrent_url_is_fetched_directly_without_a_mirror(app: MockTsundokuAppState) -> None:
    """Every non-development deployment must behave exactly as before."""
    assert app.flags.TORRENT_MIRROR_URL is None
    app.session.stub("GET", REAL_TORRENT_URL, body=REAL_BYTES)

    assert await app.dl_client.fetch_torrent(REAL_TORRENT_URL) == REAL_BYTES
    assert not app.session.requests_for("POST")


async def test_magnet_is_returned_untouched_without_a_mirror(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    assert await app.dl_client.get_magnet(REAL_MAGNET) == REAL_MAGNET
    app.session.assert_no_requests()


async def test_torrent_url_is_exchanged_at_the_mirror(app: MockTsundokuAppState, monkeypatch: pytest.MonkeyPatch) -> None:
    use_mirror(app, monkeypatch)
    app.session.stub("GET", REAL_TORRENT_URL, body=REAL_BYTES)
    app.session.stub("POST", f"{MIRROR}/mirror", body=SYNTHETIC_BYTES)

    assert await app.dl_client.fetch_torrent(REAL_TORRENT_URL) == SYNTHETIC_BYTES

    # The app fetches the source itself and posts the bytes on, so the mirror
    # never has to reach the source tracker.
    posted = app.session.requests_for("POST", MIRROR)
    assert len(posted) == 1
    assert posted[0].kwargs["data"] == REAL_BYTES


async def test_magnet_is_posted_to_the_mirror_verbatim(app: MockTsundokuAppState, monkeypatch: pytest.MonkeyPatch) -> None:
    """A magnet has nothing to fetch; the mirror reads its display name."""
    use_mirror(app, monkeypatch)
    app.session.stub("POST", f"{MIRROR}/mirror", body=SYNTHETIC_BYTES)

    assert await app.dl_client.fetch_torrent(REAL_MAGNET) == SYNTHETIC_BYTES

    assert not app.session.requests_for("GET")
    posted = app.session.requests_for("POST", MIRROR)
    assert posted[0].kwargs["data"] == REAL_MAGNET.encode()


async def test_get_magnet_rebuilds_from_the_synthetic_torrent(app: MockTsundokuAppState, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    """The magnet handed to the download client must describe the synthetic
    torrent, otherwise the client would join the real swarm."""
    caplog.set_level(logging.ERROR, logger="tsundoku")
    use_mirror(app, monkeypatch)
    app.session.stub("POST", f"{MIRROR}/mirror", body=SYNTHETIC_BYTES)

    magnet = await app.dl_client.get_magnet(REAL_MAGNET)

    decoded: Any = bencodepy.decode(SYNTHETIC_BYTES)
    expected = hashlib.sha1(bencodepy.encode(decoded[b"info"])).hexdigest()
    assert f"urn:btih:{expected}" in magnet
    assert "0123456789abcdef0123456789abcdef01234567" not in magnet


async def test_file_structure_comes_from_the_synthetic_torrent(app: MockTsundokuAppState, monkeypatch: pytest.MonkeyPatch) -> None:
    use_mirror(app, monkeypatch)
    app.session.stub("GET", REAL_TORRENT_URL, body=REAL_BYTES)
    app.session.stub("POST", f"{MIRROR}/mirror", body=SYNTHETIC_BYTES)

    # MockDownloadManager overrides get_file_structure with a fixture registry
    # for the poller tests, so the real implementation is invoked directly.
    assert await Manager.get_file_structure(app.dl_client, REAL_TORRENT_URL) == ["Real.Release.mkv"]


async def test_mirror_failure_is_surfaced_not_swallowed(app: MockTsundokuAppState, monkeypatch: pytest.MonkeyPatch) -> None:
    use_mirror(app, monkeypatch)
    app.session.stub("GET", REAL_TORRENT_URL, body=REAL_BYTES)
    app.session.stub("POST", f"{MIRROR}/mirror", status=502, text="could not fetch the source torrent")

    with pytest.raises(RuntimeError, match="502"):
        await app.dl_client.fetch_torrent(REAL_TORRENT_URL)
