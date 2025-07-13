import logging

from pytest import LogCaptureFixture

from tests.mock import MockTsundokuApp


async def test_all_found_are_managed(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
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


async def test_rss_cache_ends_search(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    found = await app.poller.poll()

    async with app.acquire_db() as con:
        await con.execute("DELETE FROM show_entry;")

    found_after = await app.poller.poll()

    assert len(found) > 0
    assert len(found_after) == 0


async def test_rss_cache_cleared(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    found = await app.poller.poll()

    async with app.acquire_db() as con:
        await con.execute("DELETE FROM show_entry;")

    app.poller.reset_rss_cache()
    found_after = await app.poller.poll()

    assert len(found) > 0
    assert len(found) == len(found_after)


async def test_rss_force_poll(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    found = await app.poller.poll()

    async with app.acquire_db() as con:
        await con.execute("DELETE FROM show_entry;")

    found_after = await app.poller.poll(force=True)

    assert len(found) > 0
    assert len(found) == len(found_after)
