from __future__ import annotations

import json
import logging
import os
import sqlite3
from configparser import ConfigParser
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
import subprocess
from typing import Any, AsyncGenerator, Generator, TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.asqlite import Cursor

from yoyo import get_backend, read_migrations

from . import asqlite

logger = logging.getLogger("tsundoku")


if os.getenv("IS_DOCKER"):
    fp = "data/tsundoku.db"
else:
    fp = "tsundoku.db"


@asynccontextmanager
async def acquire() -> AsyncGenerator[Cursor, None]:
    async with asqlite.connect(fp) as con:
        async with con.cursor() as cur:
            yield cur


@contextmanager
def sync_acquire() -> Generator[sqlite3.Connection, None, None]:
    with sqlite3.connect(fp) as con:
        con.row_factory = sqlite3.Row
        yield con


def spawn_shell() -> None:
    subprocess.run(["sqlite3", fp, "-header", "-column"])


def get_cfg_value(parser: ConfigParser, key: str, value: str, default=None) -> Any:
    try:
        value = parser[key][value]
    except Exception:
        return default

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


async def transfer_config() -> None:
    cfg_fp = "data/config.ini" if os.getenv("IS_DOCKER") else "config.ini"
    if not Path(cfg_fp).exists():
        return

    cfg = ConfigParser()
    cfg.read(cfg_fp)

    async with acquire() as con:
        await con.execute(
            """
            INSERT INTO
                general_config (
                    id,
                    host,
                    port,
                    update_do_check,
                    locale,
                    log_level
                )
            VALUES (
                0,
                :host,
                :port,
                :update_do_check,
                :locale,
                :log_level
            )
            ON CONFLICT (id) DO UPDATE SET
                host = :host,
                port = :port,
                update_do_check = :update_do_check,
                locale = :locale,
                log_level = :log_level;
            """,
            {
                "host": get_cfg_value(cfg, "Tsundoku", "host", "localhost"),
                "port": get_cfg_value(cfg, "Tsundoku", "port", 6439),
                "update_do_check": get_cfg_value(
                    cfg, "Tsundoku", "do_update_checks", True
                ),
                "locale": get_cfg_value(cfg, "Tsundoku", "locale", "en"),
                "log_level": get_cfg_value(cfg, "Tsundoku", "log_level", "info"),
            },
        )
        await con.execute(
            """
            INSERT INTO
                feeds_config (
                    id,
                    polling_interval,
                    complete_check_interval,
                    fuzzy_cutoff
                )
            VALUES (
                0,
                :polling_interval,
                :complete_check_interval,
                :fuzzy_cutoff
            )
            ON CONFLICT (id) DO UPDATE SET
                polling_interval = :polling_interval,
                complete_check_interval = :complete_check_interval,
                fuzzy_cutoff = :fuzzy_cutoff;
            """,
            {
                "polling_interval": get_cfg_value(
                    cfg, "Tsundoku", "polling_interval", 900
                ),
                "complete_check_interval": get_cfg_value(
                    cfg, "Tsundoku", "complete_check_interval", 15
                ),
                "fuzzy_cutoff": get_cfg_value(
                    cfg, "Tsundoku", "fuzzy_match_cutoff", 90
                ),
            },
        )
        await con.execute(
            """
            INSERT INTO
                torrent_config (
                    id,
                    client,
                    host,
                    port,
                    username,
                    password,
                    secure
                )
            VALUES (
                0,
                :client,
                :host,
                :port,
                :username,
                :password,
                :secure
            )
            ON CONFLICT (id) DO UPDATE SET
                client = :client,
                host = :host,
                port = :port,
                username = :username,
                password = :password,
                secure = :secure;
            """,
            {
                "client": get_cfg_value(cfg, "TorrentClient", "client", "qbittorrent"),
                "host": get_cfg_value(cfg, "TorrentClient", "host", "localhost"),
                "port": get_cfg_value(cfg, "TorrentClient", "port", 8112),
                "username": get_cfg_value(cfg, "TorrentClient", "username", "admin"),
                "password": get_cfg_value(cfg, "TorrentClient", "password", "password"),
                "secure": get_cfg_value(cfg, "TorrentClient", "secure", False),
            },
        )

    path = Path(cfg_fp)
    path.rename(path.with_suffix(".old"))


async def migrate() -> None:
    backend = get_backend(f"sqlite:///{fp}")
    migrations = read_migrations("migrations")
    migrations.items = migrations.items[14:]

    logger.info("Applying database migrations...")
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))

    try:
        await transfer_config()
    except Exception as e:
        logger.error(f"Error importing old configuration: {e}")

    logger.info("Database migrations applied.")
