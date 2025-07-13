import logging
from pathlib import Path

from pytest import LogCaptureFixture

from tests.mock import MockTsundokuApp
from tsundoku.config import GeneralConfig


async def test_expected_file_paths(app: MockTsundokuApp, caplog: LogCaptureFixture):
    caplog.set_level(logging.ERROR, logger="tsundoku")

    await app.poller.poll()

    app.dl_client.mark_all_torrent_complete()
    await app.downloader.check_show_entries()

    async with app.acquire_db() as con:
        rows = await con.fetchall(
            """
            SELECT file_path FROM show_entry ORDER BY id ASC;
        """
        )

    paths = (Path(r["file_path"]) for r in rows)

    expected_parts = (
        ("anime1", "Chainsaw Man", "Season 1", "Chainsaw Man - s01e12.mkv"),
        ("anime2", "Buddy Daddies", "Season 2", "Buddy Daddies - s02e04.mkv"),
        ("anime1", "NIER LOCAL", "Season 1", "NIER LOCAL - s01e02.mkv"),
        ("anime1", "NIER LOCAL", "Season 1", "NIER LOCAL - s01e03.mkv"),
    )

    for path in paths:
        assert path.parts in expected_parts


async def test_no_season_folder(app: MockTsundokuApp, caplog: LogCaptureFixture):
    caplog.set_level(logging.ERROR, logger="tsundoku")

    config = await GeneralConfig.retrieve(app)  # type: ignore
    config.use_season_folder = False
    await config.save()
    await app.downloader.update_config()

    await app.poller.poll()

    app.dl_client.mark_all_torrent_complete()
    await app.downloader.check_show_entries()

    async with app.acquire_db() as con:
        rows = await con.fetchall(
            """
            SELECT file_path FROM show_entry ORDER BY id ASC;
        """
        )

    paths = (Path(r["file_path"]) for r in rows)

    expected_parts = (
        ("anime1", "Chainsaw Man", "Chainsaw Man - s01e12.mkv"),
        ("anime2", "Buddy Daddies", "Buddy Daddies - s02e04.mkv"),
        ("anime1", "NIER LOCAL", "NIER LOCAL - s01e02.mkv"),
        ("anime1", "NIER LOCAL", "NIER LOCAL - s01e03.mkv"),
    )

    for path in paths:
        assert path.parts in expected_parts
