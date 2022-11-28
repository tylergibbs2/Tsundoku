from __future__ import annotations

import inspect
import logging
import sqlite3
from typing import Any, Dict, Optional

from tsundoku.constants import VALID_SPEEDS
from tsundoku.database import acquire, sync_acquire

logger = logging.getLogger("tsundoku")


class ConfigCheckFailure(Exception):
    ...


class ConfigInvalidKey(Exception):
    ...


class Config:
    TABLE_NAME = None

    def __init__(self, keys: Dict[str, Any]) -> None:
        self.keys = keys

        self.valid_keys = set(self.keys.keys())

    def __getitem__(self, key: str) -> Any:
        return self.keys[key]

    def __hash__(self) -> int:
        return hash(self.keys.values())

    def __setitem__(self, key: str, value: str) -> None:
        if key not in self.valid_keys:
            raise ConfigInvalidKey(f"Invalid key '{key}'")

        self.keys[key] = value

    def get(self, key: str, default: Any = None) -> Optional[Any]:
        return self.keys.get(key, default)

    def update(self, other: Dict[str, str]) -> None:
        if any(k not in self.valid_keys for k in self.valid_keys):
            raise ConfigInvalidKey(f"Invalid configuration key.")

        self.keys.update(other)

    @classmethod
    async def retrieve(cls, ensure_exists: bool = True) -> Config:
        async with acquire() as con:
            if ensure_exists:
                await con.execute(
                    f"""
                    INSERT OR IGNORE INTO
                        {cls.TABLE_NAME} (
                            id
                        )
                    VALUES (0);
                """
                )

            await con.execute(
                f"""
                SELECT * FROM {cls.TABLE_NAME};
            """
            )
            row: sqlite3.Row = await con.fetchone()

        return cls({k: row[k] for k in row.keys()})

    @classmethod
    def sync_retrieve(cls, ensure_exists: bool = True) -> Config:
        with sync_acquire() as con:
            if ensure_exists:
                con.execute(
                    f"""
                    INSERT OR IGNORE INTO
                        {cls.TABLE_NAME} (
                            id
                        )
                    VALUES (0);
                """
                )

            cur = con.execute(
                f"""
                SELECT * FROM {cls.TABLE_NAME};
            """
            )
            row: sqlite3.Row = cur.fetchone()

        if row is None:
            return cls({})

        return cls({k: row[k] for k in row.keys()})

    async def save(self) -> None:
        for key, value in self.keys.items():
            func = getattr(self, f"check_{key}", None)
            if func is None:
                continue

            try:
                if inspect.iscoroutinefunction(func):
                    res = await func(value)
                else:
                    res = func(value)
            except Exception:
                raise ConfigCheckFailure(f"'{key}' failed when checking.")

            if res is False:
                raise ConfigCheckFailure(f"'{key}' is invalid.")

        sets = ", ".join(f"{col} = ?" for col in self.keys)
        async with acquire() as con:
            await con.execute(
                f"""
                UPDATE
                    {self.TABLE_NAME}
                SET
                    {sets}
                WHERE id = 0;
            """,
                *self.keys.values(),
            )


class GeneralConfig(Config):
    TABLE_NAME = "general_config"

    def check_port(self, value: str) -> bool:
        return 1 <= int(value) <= 65535

    def check_log_level(self, value: str) -> bool:
        if value in ("error", "warning", "info", "debug"):
            level = getattr(logging, value.upper())
            logger.setLevel(level)
            return True

        return False


class FeedsConfig(Config):
    TABLE_NAME = "feeds_config"

    def check_polling_interval(self, value: str) -> bool:
        return int(value) >= 1

    def check_complete_check_interval(self, value: str) -> bool:
        return int(value) >= 1

    def check_fuzzy_cutoff(self, value: str) -> bool:
        return 0 <= int(value) <= 100

    def check_seed_ratio_limit(self, value: str) -> bool:
        return float(value) >= 0.0


class TorrentConfig(Config):
    TABLE_NAME = "torrent_config"

    def check_client(self, value: str) -> bool:
        return value in ("deluge", "transmission", "qbittorrent")

    def check_port(self, value: str) -> bool:
        return 1 <= int(value) <= 65535


class EncodeConfig(Config):
    TABLE_NAME = "encode_config"

    def check_maximum_encodes(self, value: str) -> bool:
        return int(value) >= 1

    def check_speed_preset(self, value: str) -> bool:
        return value in VALID_SPEEDS

    def check_quality_preset(self, value: str) -> bool:
        return value in ("high", "low", "moderate")

    def check_hour_start(self, value: str) -> bool:
        hour_end = self["hour_end"]
        if hour_end:
            return int(hour_end) > int(value)

        return True

    def check_hour_end(self, value: str) -> bool:
        hour_start = self["hour_start"]
        if hour_start:
            return int(hour_start) < int(value)

        return True
