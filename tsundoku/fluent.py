import sqlite3
from typing import Any, List

from fluent.runtime import FluentLocalization, FluentResourceLoader

from tsundoku.config import GeneralConfig


def get_injector(resources: List[str]) -> Any:
    try:
        cfg = GeneralConfig.sync_retrieve()
        locale = cfg.get("locale", default="en")
    except sqlite3.OperationalError:
        locale = "en"

    loader = FluentResourceLoader("l10n/{locale}")

    resources = [f"{r}.ftl" for r in resources]

    fluent: Any = FluentLocalization([locale, "en"], resources, loader)
    fluent._ = fluent.format_value

    return fluent
