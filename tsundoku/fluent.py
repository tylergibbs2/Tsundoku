from __future__ import annotations

from typing import Dict, Optional

from fluent.runtime import FluentLocalization


class CustomFluentLocalization(FluentLocalization):
    preferred_locale: str

    def __init__(self, preferred_locale: str, *args, **kwargs):
        self.preferred_locale = preferred_locale
        super().__init__(*args, **kwargs)

    def _(self, key: str, args: Optional[Dict] = None) -> str:
        return self.format_value(key, args)
