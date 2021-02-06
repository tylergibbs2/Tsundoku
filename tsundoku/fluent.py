from pathlib import Path
from typing import List

from fluent.runtime import FluentLocalization, FluentResourceLoader


def get_injector(locale: str, resources: List[str]):
    locale_dir = Path.cwd() / "l10n/{locale}"
    loader = FluentResourceLoader(str(locale_dir))

    resources = [f"{r}.ftl" for r in resources]

    fluent = FluentLocalization([locale], resources, loader)
    fluent._ = fluent.format_value

    return fluent
