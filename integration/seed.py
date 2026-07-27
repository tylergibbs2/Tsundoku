"""Seed a Tsundoku database for the compose test environment.

Run from the repo root with the same DATA_DIR the app will use:

    uv run python integration/seed.py

Idempotent: every step checks before it writes, so re-running after changing
something in the UI only fills in what is missing.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Run directly from the repo root without needing PYTHONPATH set.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tsundoku.app import TsundokuAppState, insert_user
from tsundoku.config import TorrentConfig
from tsundoku.constants import DATA_DIR, DATABASE_FILE_NAME
from tsundoku.database import migrate
from tsundoku.manager import Library, PathMapping

REPO = Path(__file__).resolve().parent.parent
DEVDATA = REPO / ".devdata"
DOWNLOADS = DEVDATA / "downloads"
LIBRARY = DEVDATA / "library"

#: What the clients call the download directory inside their containers. The
#: host sees the same files under DEVDATA, which is the mismatch the mapping
#: exists to bridge -- see compose.test.yml.
CLIENT_DOWNLOAD_PREFIX = "/downloads"

USERNAME = "admin"
PASSWORD = "adminadmin"

TORRENT_CLIENT = {
    "client": "qbittorrent",
    "host": "localhost",
    "port": 8080,
    "username": "admin",
    "password": "adminadmin",
    "secure": False,
}

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("seed")


async def ensure_user(app: TsundokuAppState) -> None:
    async with app.acquire_db() as con:
        count = await con.fetchval("SELECT COUNT(*) FROM users;")

    if count:
        logger.info("user           : already present, left alone")
        return

    await insert_user(USERNAME, PASSWORD)
    logger.info(f"user           : created {USERNAME} / {PASSWORD}")


async def ensure_library(app: TsundokuAppState) -> None:
    """Point the default library at the dev directory.

    The libraries migration seeds a placeholder row at '/', which is unusable
    as a destination -- moves into it fail with EROFS on macOS and need root
    on Linux. Repointing that row rather than adding a second one keeps a
    single obvious default, so a show created against "the first library"
    cannot silently end up aimed at '/'.
    """
    libraries = await Library.all(app)

    for library in libraries:
        if library.folder == LIBRARY:
            await library.set_default()
            logger.info(f"library        : already present -> {LIBRARY}")
            return

    if libraries:
        existing = libraries[0]
        previous = existing.folder
        existing.folder = LIBRARY
        await existing.save()
        await existing.set_default()
        logger.info(f"library        : repointed {previous} -> {LIBRARY}")
        return

    await Library.new(app, LIBRARY, is_default=True)
    logger.info(f"library        : created (default) -> {LIBRARY}")


async def ensure_path_mapping(app: TsundokuAppState) -> None:
    for mapping in await PathMapping.all(app):
        if mapping.remote_prefix == CLIENT_DOWNLOAD_PREFIX:
            logger.info(f"path mapping   : already present -> {mapping.remote_prefix} -> {mapping.local_prefix}")
            return

    await PathMapping.new(app, CLIENT_DOWNLOAD_PREFIX, str(DOWNLOADS))
    logger.info(f"path mapping   : created -> {CLIENT_DOWNLOAD_PREFIX} -> {DOWNLOADS}")


async def ensure_torrent_config(app: TsundokuAppState) -> None:
    cfg = await TorrentConfig.retrieve(app)
    for key, value in TORRENT_CLIENT.items():
        setattr(cfg, key, value)
    await cfg.save()
    logger.info(f"torrent client : {TORRENT_CLIENT['client']} at {TORRENT_CLIENT['host']}:{TORRENT_CLIENT['port']}")


def ensure_offline_sources() -> None:
    """Stop the poller reaching for the real nyaa/SubsPlease feeds.

    get_all_sources copies the bundled default sources in on first run unless
    a COPIED marker already exists. Creating the marker with no source files
    beside it leaves the poller with nothing to poll, which is what an
    environment driven by pasted links wants.
    """
    sources = DATA_DIR / "sources"
    sources.mkdir(parents=True, exist_ok=True)

    marker = sources / "COPIED"
    if marker.exists():
        logger.info("rss sources    : already suppressed")
        return

    marker.touch()
    logger.info(f"rss sources    : suppressed (marker at {marker})")


async def main() -> None:
    for directory in (DOWNLOADS, LIBRARY):
        directory.mkdir(parents=True, exist_ok=True)

    await migrate(DATA_DIR / DATABASE_FILE_NAME)

    app = TsundokuAppState()
    await ensure_user(app)
    await ensure_library(app)
    await ensure_path_mapping(app)
    await ensure_torrent_config(app)
    ensure_offline_sources()

    logger.info("")
    logger.info("Ready. Start the app with:")
    logger.info("    TORRENT_MIRROR_URL=http://localhost:8081 uv run python -m tsundoku")


if __name__ == "__main__":
    asyncio.run(main())
