from typing import Any

from fluent.runtime import FluentLocalization


class CustomFluentLocalization(FluentLocalization):
    preferred_locale: str

    def __init__(self, preferred_locale: str, *args: Any, **kwargs: Any) -> None:
        self.preferred_locale = preferred_locale
        super().__init__(*args, **kwargs)

    def _(self, key: str, args: dict | None = None) -> str:
        return self.format_value(key, args)
