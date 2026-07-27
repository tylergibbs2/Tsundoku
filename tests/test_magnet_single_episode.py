"""Magnets are a single-episode-only input, and say so when they are not.

A magnet carries an info hash and an optional display name -- never a file
list. Recovering the real structure of a multi-file magnet would require
fetching metadata from the swarm or a third-party torrent cache, so Tsundoku
supports exactly what a magnet can honestly describe: one file.
"""

import logging
from urllib.parse import quote

import pytest

from tests.mock import MockTsundokuAppState
from tsundoku.dl_client import Manager
from tsundoku.dl_client.client import magnet_display_name
from tsundoku.nyaa import MagnetIsNotSingleEpisodeError, SearchResult

SINGLE = "[SubsPlease] Some Show - 07 (1080p) [ABCD1234].mkv"
BATCH = "[GyroSubs] Some Show 843-854 (BD 1080p 10-bit Opus)"


def magnet_for(name: str, info_hash: str = "0" * 40) -> str:
    return f"magnet:?xt=urn:btih:{info_hash}&dn={quote(name)}&tr=http%3A%2F%2Ftracker.example%2Fannounce"


def test_display_name_is_read_from_the_magnet() -> None:
    assert magnet_display_name(magnet_for(SINGLE)) == SINGLE
    assert magnet_display_name("magnet:?xt=urn:btih:" + "0" * 40) is None


async def test_file_structure_of_a_magnet_is_its_display_name(app: MockTsundokuAppState) -> None:
    """No network involved: the name is already in the magnet."""
    assert await Manager.get_file_structure(app.dl_client, magnet_for(SINGLE)) == [SINGLE]
    app.session.assert_no_requests()


async def test_a_magnet_without_a_display_name_is_rejected(app: MockTsundokuAppState) -> None:
    with pytest.raises(ValueError, match="no display name"):
        await Manager.get_file_structure(app.dl_client, "magnet:?xt=urn:btih:" + "0" * 40)


async def test_single_episode_magnet_resolves_to_one_episode(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    result = SearchResult.from_necessary(app, 1, magnet_for(SINGLE))
    assert await result.get_episodes() == [7]


async def test_batch_magnet_is_refused_with_an_actionable_message(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    """Silently adding nothing -- the old behaviour -- is the worst answer."""
    caplog.set_level(logging.ERROR, logger="tsundoku")

    result = SearchResult.from_necessary(app, 1, magnet_for(BATCH))

    with pytest.raises(MagnetIsNotSingleEpisodeError, match="single-episode releases only"):
        await result.get_episodes()


async def test_a_torrent_link_yielding_no_episodes_is_still_tolerated(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    """The restriction is about magnets; a .torrent may legitimately hold
    nothing episodic and must not start raising."""
    caplog.set_level(logging.ERROR, logger="tsundoku")

    result = SearchResult.from_necessary(app, 1, "https://nyaa.si/download/1.torrent")
    app.dl_client.set_file_structure("https://nyaa.si/download/1.torrent", ["extras.nfo"])

    assert await result.get_episodes() == []
