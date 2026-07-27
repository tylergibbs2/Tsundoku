from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from tests.mock import (
    MockTsundokuAppState,
    filesystem,
    mock_feedparser_parse,
    mock_get_all_sources,
)


@pytest_asyncio.fixture(name="app")
async def create_app(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[MockTsundokuAppState, None]:
    monkeypatch.setattr("feedparser.parse", mock_feedparser_parse)
    monkeypatch.setattr("tsundoku.feeds.poller.get_all_sources", mock_get_all_sources)

    monkeypatch.setattr("pathlib.Path.symlink_to", filesystem.mock_symlink_to)
    monkeypatch.setattr("pathlib.Path.mkdir", filesystem.mock_mkdir)
    monkeypatch.setattr(
        "tsundoku.feeds.downloader.Downloader.resolve_file",
        filesystem.mock_resolve_file,
    )
    monkeypatch.setattr("aiofiles.os.rename", filesystem.mock_rename)
    monkeypatch.setattr("tsundoku.feeds.downloader.move", filesystem.mock_move)

    app = MockTsundokuAppState()
    await app.setup()

    yield app

    await app.cleanup()
