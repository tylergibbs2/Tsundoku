from asyncio import QueueFull
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

from tsundoku.config import GeneralConfig
from tsundoku.constants import DATA_DIR, LOGGING_FILE_NAME

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

    cfg = GeneralConfig.sync_retrieve(app, ensure_exists=True)

    logger.propagate = True
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(f"{DATA_DIR / LOGGING_FILE_NAME}", encoding="utf-8")
    file_handler.set_name("file")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.set_name("stream")
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(cfg.log_level.upper())
    logger.addHandler(stream_handler)

    socket_handler = SocketHandler(app)
    socket_handler.set_name("socket")
    socket_handler.setFormatter(formatter)
    socket_handler.setLevel(cfg.log_level.upper())
    logger.addHandler(socket_handler)

    logger.debug("Logging successfully configured")
