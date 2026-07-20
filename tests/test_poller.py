import logging

import pytest

from tests.mock import MockTsundokuAppState


async def test_all_found_are_managed(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    found = await app.poller.poll()

    app.dl_client.mark_all_torrent_complete()
    await app.downloader.check_show_entries()

    async with app.acquire_db() as con:
        entry_count = await con.fetchval(
            """
            SELECT COUNT(*) FROM show_entry;
        """
        )

    assert len(found) == entry_count


async def test_rss_cache_ends_search(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    found = await app.poller.poll()

    async with app.acquire_db() as con:
        await con.execute("DELETE FROM show_entry;")

    found_after = await app.poller.poll()

    assert len(found) > 0
    assert len(found_after) == 0


async def test_rss_cache_cleared(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    found = await app.poller.poll()

    async with app.acquire_db() as con:
        await con.execute("DELETE FROM show_entry;")

    app.poller.reset_rss_cache()
    found_after = await app.poller.poll()

    assert len(found) > 0
    assert len(found) == len(found_after)


async def test_rss_force_poll(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    found = await app.poller.poll()

    async with app.acquire_db() as con:
        await con.execute("DELETE FROM show_entry;")

    found_after = await app.poller.poll(force=True)

    assert len(found) > 0
    assert len(found) == len(found_after)
