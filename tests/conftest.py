import inspect
from typing import AsyncGenerator

import pytest
import pytest_asyncio

from tests.mock import MockTsundokuApp, mock_get_all_sources, mock_feedparser_parse
from tests.mock import filesystem


def pytest_collection_modifyitems(config, items):
    for item in items:
        if inspect.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


@pytest_asyncio.fixture(name="app", scope="function")
async def create_app(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[MockTsundokuApp, None]:
    monkeypatch.setattr("feedparser.parse", mock_feedparser_parse)
    monkeypatch.setattr("tsundoku.feeds.poller.get_all_sources", mock_get_all_sources)

    monkeypatch.setattr("pathlib.Path.symlink_to", filesystem.mock_symlink_to)
    monkeypatch.setattr(
        "tsundoku.feeds.downloader.Downloader.resolve_file",
        filesystem.mock_resolve_file,
    )
    monkeypatch.setattr("aiofiles.os.rename", filesystem.mock_rename)
    monkeypatch.setattr("tsundoku.feeds.downloader.move", filesystem.mock_move)

    app = MockTsundokuApp()
    await app.setup()

    yield app

    await app.cleanup()
