from __future__ import annotations

import importlib
import importlib.util
import logging
from typing import Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

    app: TsundokuApp
else:
    from quart import current_app as app


import tsundoku.exceptions as exceptions

logger = logging.getLogger("tsundoku")


class ParserStub:
    name: str
    url: str
    version: str
    app: TsundokuApp

    _last_etag: Optional[str]
    _last_modified: Optional[str]
    _most_recent_hash: Optional[str]

    def get_show_name(self, file_name: str) -> str:
        return ""

    def get_episode_number(self, file_name: str) -> Optional[int]:
        ...

    def get_link_location(self, item: dict) -> str:
        return ""

    def get_file_name(self, item: dict) -> str:
        return ""

    def ignore_logic(self, item: dict) -> bool:
        return True


def load_parsers(parsers: List[str]) -> None:
    """
    Load all of the custom RSS parsers into the app.
    """
    app.rss_parsers = []

    required_attrs = ("name", "url", "version", "get_show_name", "get_episode_number")

    for parser in parsers:
        spec: Any = importlib.util.find_spec(parser)

        if spec is None:
            logger.error(f"Parser `{parser}` Not Found")
            raise exceptions.ParserNotFound(parser)

        lib = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(lib)
        except Exception:
            logger.error(f"Parser `{parser}` Failed")
            continue

        try:
            setup = getattr(lib, "setup")
        except AttributeError:
            logger.error(f"Parser `{parser}` Missing Setup Function")
            continue

        try:
            new_context = app.app_context()
            parser_object = setup(new_context.app)
            for func in required_attrs:
                if not hasattr(parser_object, func):
                    logger.error(f"Parser `{parser}` missing attr/function `{func}`")
                    continue
            app.rss_parsers.append(parser_object)
        except Exception as e:
            logger.error(f"Parser `{parser}` Failed: {e}")
            continue

        logger.info("Loaded Parser `{0.name} v{0.version}`".format(parser_object))
