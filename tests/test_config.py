import logging

import pytest
from pytest import LogCaptureFixture

from tests.mock import MockTsundokuApp
from tsundoku.config import (
    ConfigCheckFailError,
    EncodeConfig,
    FeedsConfig,
    GeneralConfig,
    TorrentConfig,
)


async def test_async_retrieve_general_config(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    await GeneralConfig.retrieve(app)  # type: ignore


async def test_async_retrieve_feeds_config(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    await FeedsConfig.retrieve(app)  # type: ignore


async def test_async_retrieve_torrent_config(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    await TorrentConfig.retrieve(app)  # type: ignore


async def test_async_retrieve_encode_config(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    await EncodeConfig.retrieve(app)  # type: ignore


def test_sync_retrieve_general_config(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    GeneralConfig.sync_retrieve(app)  # type: ignore


def test_sync_retrieve_feeds_config(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    FeedsConfig.sync_retrieve(app)  # type: ignore


def test_sync_retrieve_torrent_config(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    TorrentConfig.sync_retrieve(app)  # type: ignore


def test_sync_retrieve_encode_config(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    EncodeConfig.sync_retrieve(app)  # type: ignore


async def test_general_config_invalid_port(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    config = await GeneralConfig.retrieve(app)  # type: ignore
    config.port = 1023
    with pytest.raises(ConfigCheckFailError):
        await config.save()


async def test_general_config_valid_port(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    config = await GeneralConfig.retrieve(app)  # type: ignore
    config.port = 1024
    await config.save()
