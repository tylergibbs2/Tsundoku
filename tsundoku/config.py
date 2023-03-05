from __future__ import annotations

import inspect
import logging
import sqlite3
from typing import Any, Dict, Optional, TYPE_CHECKING
from typing_extensions import Self

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

from tsundoku.constants import VALID_SPEEDS

logger = logging.getLogger("tsundoku")


class ConfigCheckFailure(Exception):
    ...


class ConfigInvalidKey(Exception):
    ...


class Config:
    app: TsundokuApp
    TABLE_NAME = None

    def __init__(self, app: TsundokuApp, keys: Dict[str, Any]) -> None:
        super().__setattr__("app", app)
        super().__setattr__("keys", keys)

        super().__setattr__("valid_keys", set(self.keys.keys()))

    def __getattribute__(self, __name: str) -> Any:
        keys = super().__getattribute__("keys")
        if __name in keys:
            return keys[__name]

        return super().__getattribute__(__name)

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name not in self.valid_keys:
            raise ConfigInvalidKey(f"Invalid key '{__name}'")

        self.keys[__name] = __value

    def __hash__(self) -> int:
        return hash(self.keys.values())

    def update(self, other: Dict[str, str]) -> None:
        if any(k not in self.valid_keys for k in self.valid_keys):
            raise ConfigInvalidKey("Invalid configuration key.")

        self.keys.update(other)

    @classmethod
    async def retrieve(cls, app: TsundokuApp, ensure_exists: bool = True) -> Self:
        async with app.acquire_db() as con:
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

            row = await con.fetchone(
                f"""
                SELECT * FROM {cls.TABLE_NAME};
            """
            )

        return cls(app, {k: row[k] for k in row.keys()})

    @classmethod
    def sync_retrieve(cls, app: TsundokuApp, ensure_exists: bool = True) -> Self:
        with app.sync_acquire_db() as con:
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
            return cls(app, {})

        return cls(app, {k: row[k] for k in row.keys()})

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
        async with self.app.acquire_db() as con:
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

    host: str
    port: int
    update_do_check: bool
    locale: str
    log_level: str
    default_desired_format: str
    default_desired_folder: str
    unwatch_when_finished: bool

    def check_port(self, value: str) -> bool:
        return 1 <= int(value) <= 65535

    def check_log_level(self, value: str) -> bool:
        if value in ("error", "warning", "info", "debug"):
            for handler in logger.handlers:
                if handler.name in ("stream", "socket"):
                    handler.setLevel(value.upper())

            return True

        return False

    def check_locale(self, value: str) -> bool:
        self.app.flags.LOCALE = value
        return True


class FeedsConfig(Config):
    TABLE_NAME = "feeds_config"

    polling_interval: int
    complete_check_interval: int
    fuzzy_cutoff: int
    seed_ratio_limit: float

    def check_polling_interval(self, value: str) -> bool:
        return int(value) >= 180

    def check_complete_check_interval(self, value: str) -> bool:
        return int(value) >= 1

    def check_fuzzy_cutoff(self, value: str) -> bool:
        return 0 <= int(value) <= 100

    def check_seed_ratio_limit(self, value: str) -> bool:
        return float(value) >= 0.0


class TorrentConfig(Config):
    TABLE_NAME = "torrent_config"

    client: str
    host: str
    port: int
    username: Optional[str]
    password: Optional[str]
    secure: bool

    def check_client(self, value: str) -> bool:
        return value in ("deluge", "transmission", "qbittorrent")

    def check_port(self, value: str) -> bool:
        return 1 <= int(value) <= 65535


class EncodeConfig(Config):
    TABLE_NAME = "encode_config"

    enabled: bool
    quality_preset: str
    speed_preset: str
    maximum_encodes: int
    timed_encoding: bool
    hour_start: int
    hour_end: int

    def check_maximum_encodes(self, value: str) -> bool:
        return int(value) >= 1

    def check_speed_preset(self, value: str) -> bool:
        return value in VALID_SPEEDS

    def check_quality_preset(self, value: str) -> bool:
        return value in ("high", "low", "moderate")

    def check_hour_start(self, value: str) -> bool:
        hour_end = self.hour_end
        if hour_end:
            return int(hour_end) > int(value)

        return True

    def check_hour_end(self, value: str) -> bool:
        hour_start = self.hour_start
        if hour_start:
            return int(hour_start) < int(value)

        return True
