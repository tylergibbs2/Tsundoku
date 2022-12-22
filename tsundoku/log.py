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
        for queue in self.app.connected_websockets:
            try:
                queue.put_nowait(self.format(record))
            except QueueFull:
                continue


def setup_logging(app: TsundokuApp) -> None:
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    try:
        cfg = GeneralConfig.sync_retrieve(ensure_exists=True)
        level = cfg.get("log_level") or "info"
    except Exception:
        level = "info"

    logger.propagate = True
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler("tsundoku.log", encoding="utf-8")
    file_handler.set_name("file")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.set_name("stream")
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level.upper())
    logger.addHandler(stream_handler)

    socket_handler = SocketHandler(app)
    socket_handler.set_name("socket")
    socket_handler.setFormatter(formatter)
    socket_handler.setLevel(level.upper())
    logger.addHandler(socket_handler)

    logger.debug("Logging successfully configured")
