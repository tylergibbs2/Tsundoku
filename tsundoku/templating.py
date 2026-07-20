from __future__ import annotations

from collections.abc import Callable
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from tsundoku import __version__ as version

if TYPE_CHECKING:
    from tsundoku.app import TsundokuAppState

logger = logging.getLogger("tsundoku")

TEMPLATES_DIR = Path(__file__).parent / "blueprints" / "ux" / "templates"
STATIC_URL_PATH = "/ux/static"
_STATIC_JS_DIR = Path("tsundoku", "blueprints", "ux", "static", "js")

_NAMED_ROUTES = {
    "ux.index": "/",
    "ux.login": "/login",
    "ux.register": "/register",
    "ux.logout": "/logout",
}

_templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

FLASH_SESSION_KEY = "_flashes"


def flash(request: Request, message: str, category: str = "message") -> None:
    """Queue a flash ``message`` under ``category`` for the next render."""
    flashes: list[list[str]] = request.session.setdefault(FLASH_SESSION_KEY, [])
    flashes.append([category, message])


def get_flashed_messages(request: Request, with_categories: bool = False) -> list[Any]:
    """Pop and return queued flash messages, mirroring Flask/Quart semantics."""
    flashes: list[list[str]] = request.session.pop(FLASH_SESSION_KEY, [])
    if with_categories:
        return [(category, message) for category, message in flashes]

    return [message for _category, message in flashes]


def _resolve_bundle_filename(state: TsundokuAppState, filename: str) -> str:
    """Rewrite ``js/root.js`` to its content-hashed build output, if present."""
    if filename != "js/root.js":
        return filename

    if state.cached_bundle_hash is not None and not state.flags.IS_DEBUG:
        return f"js/root.{state.cached_bundle_hash}.js"

    if not _STATIC_JS_DIR.exists():
        logger.error("Could not find static JS folder!")
        return filename

    for file in _STATIC_JS_DIR.glob("root.*.js"):
        split = file.name.split(".")
        if len(split) == 2:
            return filename

        state.cached_bundle_hash = split[1]
        return f"js/root.{state.cached_bundle_hash}.js"

    return filename


def _make_url_for(state: TsundokuAppState) -> Callable[..., str]:
    def url_for(name: str, **params: str) -> str:
        if name == "ux.static":
            filename = _resolve_bundle_filename(state, params["filename"])
            return f"{STATIC_URL_PATH}/{filename}"

        return _NAMED_ROUTES[name]

    return url_for


def static_url(filename: str) -> str:
    """Build a static asset URL outside of a request/template context."""
    return f"{STATIC_URL_PATH}/{filename}"


def render(
    state: TsundokuAppState,
    request: Request,
    template_name: str,
    **context: object,
) -> HTMLResponse:
    """Render ``template_name`` with Tsundoku's shared template context."""
    fluent = state.get_fluent()

    full_context: dict[str, object] = {
        "url_for": _make_url_for(state),
        "get_flashed_messages": lambda with_categories=False: get_flashed_messages(request, with_categories),
        "_": fluent.format_value,
        "LOCALE": state.flags.LOCALE,
        "stats": {"version": version},
        "docker": state.flags.IS_DOCKER,
        "update_info": state.flags.UPDATE_INFO,
        **context,
    }

    return _templates.TemplateResponse(request, template_name, full_context)
