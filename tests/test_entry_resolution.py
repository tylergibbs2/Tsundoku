"""What happens to an entry whose downloaded file cannot be found.

Before these paths existed such an entry was re-checked forever: no log line,
no state change, and nothing in the UI to show anything was wrong.
"""

from datetime import UTC, datetime, timedelta
import logging
from pathlib import Path

import pytest

from tests.mock import MockTsundokuAppState
from tsundoku.feeds.downloader import STALL_GRACE_SECONDS
from tsundoku.manager import Entry, EntryState

TORRENT_HASH = "0123456789abcdef0123456789abcdef01234567"


async def make_entry(app: MockTsundokuAppState, episode: int, state: EntryState, file_path: str | None = None, torrent_hash: str = TORRENT_HASH) -> Entry:
    async with app.acquire_db() as con, con.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO show_entry (show_id, episode, current_state, torrent_hash, file_path)
            VALUES (1, ?, ?, ?, ?);
            """,
            episode,
            state.value,
            torrent_hash,
            file_path,
        )
        await cur.execute("SELECT * FROM show_entry WHERE id = ?;", cur.lastrowid)
        record = await cur.fetchone()

    return Entry.from_record(app, record)


async def age_entry(app: MockTsundokuAppState, entry: Entry, seconds: float) -> Entry:
    """Backdate an entry's last_update so the stall allowance is exceeded."""
    stale = datetime.now(UTC) - timedelta(seconds=seconds)
    async with app.acquire_db() as con:
        await con.execute("UPDATE show_entry SET last_update = ? WHERE id = ?;", stale.strftime("%Y-%m-%d %H:%M:%S"), entry.id)
        record = await con.fetchone("SELECT * FROM show_entry WHERE id = ?;", entry.id)

    return Entry.from_record(app, record)


async def test_duplicate_entry_adopts_the_already_handled_file(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    """Re-adding a torrent that was already processed should settle, not spin."""
    caplog.set_level(logging.INFO, logger="tsundoku")

    handled = "/library/Show/Season 1/Show - s01e03.mkv"
    await make_entry(app, episode=3, state=EntryState.completed, file_path=handled)
    duplicate = await make_entry(app, episode=3, state=EntryState.downloading)

    await app.downloader.handle_unresolvable(duplicate, "file is gone")

    assert duplicate.state == EntryState.completed
    assert duplicate.file_path == Path(handled)


async def test_same_torrent_for_a_different_episode_fails_loudly(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    """A single-file torrent cannot satisfy two different episodes."""
    caplog.set_level(logging.ERROR, logger="tsundoku")

    await make_entry(app, episode=3, state=EntryState.completed, file_path="/library/Show/Season 1/Show - s01e03.mkv")
    mismatched = await make_entry(app, episode=20, state=EntryState.downloading)

    await app.downloader.handle_unresolvable(mismatched, "file is gone")

    assert mismatched.state == EntryState.failed
    assert "already consumed" in caplog.text
    assert "episode 20" in caplog.text


async def test_an_entry_still_within_its_allowance_keeps_waiting(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    """The client can report completion a moment before the file is readable."""
    caplog.set_level(logging.WARNING, logger="tsundoku")

    entry = await make_entry(app, episode=5, state=EntryState.downloading)
    await app.downloader.handle_unresolvable(entry, "not there yet")

    assert entry.state == EntryState.downloading
    assert "will retry" in caplog.text


async def test_a_stalled_entry_is_eventually_failed(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    entry = await make_entry(app, episode=5, state=EntryState.downloading)
    entry = await age_entry(app, entry, STALL_GRACE_SECONDS * 10)

    await app.downloader.handle_unresolvable(entry, "no file for episode 5 could be found at `/downloads/x.mkv`")

    assert entry.state == EntryState.failed
    assert "unresolved since" in caplog.text
    assert "no file for episode 5" in caplog.text


async def test_entries_sharing_a_batch_torrent_do_not_consume_each_other(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    """A different torrent hash must never be treated as the same content."""
    caplog.set_level(logging.ERROR, logger="tsundoku")

    await make_entry(app, episode=3, state=EntryState.completed, file_path="/library/Show/Season 1/Show - s01e03.mkv", torrent_hash="a" * 40)
    other = await make_entry(app, episode=4, state=EntryState.downloading, torrent_hash="b" * 40)

    assert await app.downloader.find_consuming_entry(other) is None


async def test_an_unfinished_sibling_does_not_count_as_a_consumer(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    """Only entries that took possession of the file matter; a sibling still
    downloading has not renamed anything."""
    caplog.set_level(logging.ERROR, logger="tsundoku")

    await make_entry(app, episode=3, state=EntryState.downloaded, file_path="/downloads/x.mkv")
    other = await make_entry(app, episode=4, state=EntryState.downloading)

    assert await app.downloader.find_consuming_entry(other) is None
