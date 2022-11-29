from __future__ import annotations

import logging
from asyncio import QueueFull
from logging.config import dictConfig
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

from tsundoku.config import GeneralConfig

logger = logging.getLogger("tsundoku")


class SocketHandler(logging.Handler):
    def __init__(self, app: TsundokuApp) -> None:
        self.app = app
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        if not hasattr(self.app, "logging_queue"):
            return

        if hasattr(self.app, "connected_websockets") and not len(
            self.app.connected_websockets
        ):
            return

        for queue in self.app.connected_websockets:
            try:
                queue.put_nowait(self.format(record))
            except QueueFull:
                continue


def setup_logging(app: TsundokuApp) -> None:
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    cfg = GeneralConfig.sync_retrieve(ensure_exists=True)
    level = cfg.get("log_level") or "info"

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                }
            },
            "handlers": {
                "stream": {"class": "logging.StreamHandler", "formatter": "default"},
                "file": {
                    "filename": "tsundoku.log",
                    "class": "logging.FileHandler",
                    "formatter": "default",
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "tsundoku": {
                    "handlers": ["stream", "file"],
                    "level": level.upper(),
                    "propagate": True,
                }
            },
        }
    )

    handler = SocketHandler(app)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.debug("Logging successfully configured")
