from typing import Callable, List

from fluent.runtime import FluentLocalization, FluentResourceLoader

from tsundoku.config import get_config_value


def get_injector(resources: List[str]) -> Callable:
    try:
        locale = get_config_value("Tsundoku", "locale")
    except KeyError:
        locale = "en"

    loader = FluentResourceLoader("l10n/{locale}")

    resources = [f"{r}.ftl" for r in resources]

    fluent = FluentLocalization([locale, "en"], resources, loader)
    fluent._ = fluent.format_value

    return fluent
