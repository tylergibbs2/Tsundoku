import importlib
import importlib.util
import logging
from typing import Any, List

from quart import current_app as app

import tsundoku.exceptions as exceptions

logger = logging.getLogger("tsundoku")


def load_parsers(parsers: List[str]) -> None:
    """
    Load all of the custom RSS parsers into the app.
    """
    app.rss_parsers = []

    required_attrs = (
        "name",
        "url",
        "version",
        "get_show_name",
        "get_episode_number"
    )

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
