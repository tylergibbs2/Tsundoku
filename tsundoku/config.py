import inspect
import logging
import sqlite3
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

from tsundoku.constants import VALID_MINIMUM_FILE_SIZES, VALID_SPEEDS

logger = logging.getLogger("tsundoku")


class ConfigCheckFailError(Exception):
    message: str

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.message = message


class ConfigInvalidKeyError(Exception): ...


class Config:
    app: TsundokuApp
    TABLE_NAME = None

    def __init__(self, app: TsundokuApp, keys: dict[str, Any]) -> None:
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
            raise ConfigInvalidKeyError(f"Invalid key '{__name}'")

        self.keys[__name] = __value

    def __hash__(self) -> int:
        return hash(self.keys.values())

    def update(self, other: dict[str, str]) -> None:
        if any(k not in self.valid_keys for k in self.valid_keys):
            raise ConfigInvalidKeyError("Invalid configuration key.")

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

            if inspect.iscoroutinefunction(func):
                await func(value)
            else:
                func(value)

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
    unwatch_when_finished: bool
    use_season_folder: bool

    def check_port(self, value: str) -> None:
        if isinstance(value, str) and not value.isdigit():
            raise ConfigCheckFailError(f"'{value}' is not a valid integer")

        port = int(value)
        if port < 1024:
            raise ConfigCheckFailError(f"'{port}' is less than 1024")
        if port > 65535:
            raise ConfigCheckFailError(f"'{port}' is greater than 65535")

    def check_log_level(self, value: str) -> None:
        if value in ("error", "warning", "info", "debug"):
            for handler in logger.handlers:
                if handler.name in ("stream", "socket"):
                    handler.setLevel(value.upper())

            return

        raise ConfigCheckFailError(f"'{value}' is not a valid log level")

    def check_locale(self, value: str) -> None:
        self.app.flags.LOCALE = value


class FeedsConfig(Config):
    TABLE_NAME = "feeds_config"

    polling_interval: int
    complete_check_interval: int
    fuzzy_cutoff: int
    seed_ratio_limit: float

    def check_polling_interval(self, value: str) -> None:
        if isinstance(value, str) and not value.isdigit():
            raise ConfigCheckFailError(f"'{value}' is not a valid integer")

        if int(value) < 180:
            raise ConfigCheckFailError("Polling interval must be at least 180 seconds")

    def check_complete_check_interval(self, value: str) -> None:
        if isinstance(value, str) and not value.isdigit():
            raise ConfigCheckFailError(f"'{value}' is not a valid integer")

        if int(value) < 10:
            raise ConfigCheckFailError("Completion check interval must be at least 10 seconds")

    def check_fuzzy_cutoff(self, value: str) -> None:
        if isinstance(value, str) and not value.isdigit():
            raise ConfigCheckFailError(f"'{value}' is not a valid integer")

        cutoff = int(value)
        if cutoff < 50:
            raise ConfigCheckFailError("Fuzzy cutoff percent must be at least 50%")
        if cutoff > 100:
            raise ConfigCheckFailError("Fuzzy cutoff percent can be at most 100%")

    def check_seed_ratio_limit(self, value: str) -> None:
        try:
            ratio = float(value)
        except ValueError as e:
            raise ConfigCheckFailError(f"'{value}' is not a valid float") from e

        if ratio < 0.0:
            raise ConfigCheckFailError("Seed ratio limit must be at least 0.0")


class TorrentConfig(Config):
    TABLE_NAME = "torrent_config"

    client: str
    host: str
    port: int
    username: str | None
    password: str | None
    secure: bool

    def check_client(self, value: str) -> None:
        if value not in ("deluge", "transmission", "qbittorrent"):
            raise ConfigCheckFailError(f"'{value}' is not a valid download client")

    def check_port(self, value: str) -> None:
        if isinstance(value, str) and not value.isdigit():
            raise ConfigCheckFailError(f"'{value}' is not a valid integer")

        port = int(value)
        if port < 1:
            raise ConfigCheckFailError(f"'{port}' is less than 1")
        if port > 65535:
            raise ConfigCheckFailError(f"'{port}' is greater than 65535")


class EncodeConfig(Config):
    TABLE_NAME = "encode_config"

    enabled: bool
    encoder: str
    quality_preset: str
    speed_preset: str
    maximum_encodes: int
    timed_encoding: bool
    hour_start: int
    hour_end: int
    minimum_file_size: str

    async def check_encoder(self, value: str) -> None:
        if value not in await self.app.encoder.get_available_encoders():
            raise ConfigCheckFailError(f"'{value}' is not available for encoding")

    def check_maximum_encodes(self, value: str) -> None:
        if isinstance(value, str) and not value.isdigit():
            raise ConfigCheckFailError(f"'{value}' is not a valid integer")

        max_encodes = int(value)
        if max_encodes < 1:
            raise ConfigCheckFailError("Maximum encodes must be at least 1")

    def check_speed_preset(self, value: str) -> None:
        if value not in VALID_SPEEDS:
            raise ConfigCheckFailError(f"'{value}' is not a valid speed preset")

    def check_quality_preset(self, value: str) -> None:
        if value not in ("high", "low", "moderate"):
            raise ConfigCheckFailError(f"'{value}' is not a valid quality preset")

    def check_hour_start(self, value: str) -> None:
        if isinstance(value, str) and not value.isdigit():
            raise ConfigCheckFailError(f"'{value}' is not a valid integer")

        hour_start = int(value)
        hour_end = self.hour_end
        if hour_end and hour_end <= hour_start:
            raise ConfigCheckFailError("Encode time end must be greater than encode time start")

    def check_minimum_file_size(self, value: str) -> None:
        if value not in VALID_MINIMUM_FILE_SIZES:
            raise ConfigCheckFailError(f"'{value}' is not a valid file size")

    def check_hour_end(self, value: str) -> None:
        if isinstance(value, str) and not value.isdigit():
            raise ConfigCheckFailError(f"'{value}' is not a valid integer")

        hour_end = int(value)

        hour_start = self.hour_start
        if hour_start and hour_start >= hour_end:
            raise ConfigCheckFailError("Encode time start must be less than encode time end")
