from __future__ import annotations

import logging
from asyncio import QueueFull
from logging.config import dictConfig
from typing import Any

from tsundoku.config import get_config_value

logger = logging.getLogger("tsundoku")


class SocketHandler(logging.Handler):
    def __init__(self, app: Any) -> None:
        self.app = app
        super().__init__()

    def emit(self, record: logging.LogRecord) -> None:
        if not hasattr(self.app, "logging_queue"):
            return

        if hasattr(self.app, "connected_websockets") and not len(self.app.connected_websockets):
            return

        for queue in self.app.connected_websockets:
            try:
                queue.put_nowait(self.format(record))
            except QueueFull:
                continue


def setup_logging(app: Any) -> None:
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "stream": {
                "class": "logging.StreamHandler",
                "formatter": "default"
            },
            "file": {
                "filename": "tsundoku.log",
                "class": "logging.FileHandler",
                "formatter": "default",
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "tsundoku": {
                "handlers": ["stream", "file"],
                "level": get_config_value("Tsundoku", "log_level", default="info").upper(),
                "propagate": True
            }
        }
    })

    handler = SocketHandler(app)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.debug("Logging successfully configured")
