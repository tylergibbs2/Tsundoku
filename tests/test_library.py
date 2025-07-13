import logging
from pathlib import Path

from pytest import LogCaptureFixture

from tests.mock import MockTsundokuApp
from tsundoku.manager import Library, ShowCollection


async def test_retrieve_all_libraries(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    async with app.acquire_db() as con:
        library_count = await con.fetchval(
            """
            SELECT
                COUNT(*)
            FROM
                library;
        """
        )

    libraries = await Library.all(app)  # type: ignore
    assert len(libraries) == library_count


async def test_library_folder_is_path(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    library, *_ = await Library.all(app)  # type: ignore
    assert isinstance(library.folder, Path)


async def test_only_one_default_library(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    async def count_default_libraries():
        return sum(1 for lib in await Library.all(app) if lib.is_default)  # type: ignore

    assert await count_default_libraries() == 1


async def test_only_one_default_library_from_new(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    async def count_default_libraries():
        return sum(1 for lib in await Library.all(app) if lib.is_default)  # type: ignore

    new_library = await Library.new(app, Path("/anime3"), is_default=True)  # type: ignore
    assert new_library.is_default
    assert await count_default_libraries() == 1


async def test_only_one_default_library_from_existing(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    async def count_default_libraries():
        return sum(1 for lib in await Library.all(app) if lib.is_default)  # type: ignore

    libraries = await Library.all(app)  # type: ignore
    assert len(libraries) > 1  # can't test if there's only one library in the testing data

    default, nondefault, *_ = libraries
    assert default.is_default
    assert not nondefault.is_default

    await nondefault.set_default()
    assert nondefault.is_default
    assert await count_default_libraries() == 1


async def test_all_shows_have_a_library(app: MockTsundokuApp, caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    for show in await ShowCollection.all(app):  # type: ignore
        assert show.library_id is not None
