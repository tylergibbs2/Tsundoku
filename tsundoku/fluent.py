from typing import List

from fluent.runtime import FluentLocalization, FluentResourceLoader


def get_injector(locale: str, resources: List[str]):
    loader = FluentResourceLoader("l10n/{locale}")

    resources = [f"{r}.ftl" for r in resources]

    fluent = FluentLocalization([locale, "en"], resources, loader)
    fluent._ = fluent.format_value

    return fluent
