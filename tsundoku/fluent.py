from __future__ import annotations

import sqlite3
from typing import Dict, List, Optional

from fluent.runtime import FluentLocalization, FluentResourceLoader

from tsundoku.config import GeneralConfig


class CustomFluentLocalization(FluentLocalization):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _(self, key: str, args: Optional[Dict] = None) -> str:
        return self.format_value(key, args)


def get_injector(resources: List[str]) -> CustomFluentLocalization:
    try:
        cfg = GeneralConfig.sync_retrieve()
        locale = cfg.get("locale", default="en")
    except sqlite3.OperationalError:
        locale = "en"

    loader = FluentResourceLoader("l10n/{locale}")

    resources = [f"{r}.ftl" for r in resources]

    fluent = CustomFluentLocalization([locale, "en"], resources, loader)
    return fluent
