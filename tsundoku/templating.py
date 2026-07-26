from collections.abc import Callable
import json
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
# Anchored to this file rather than the cwd, matching the static mount in
# app.py, so the manifest resolves wherever the server is started from.
_STATIC_JS_DIR = Path(__file__).parent / "blueprints" / "ux" / "static" / "js"

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


def _load_bundle_assets(state: "TsundokuAppState") -> tuple[str, list[str]]:
    """Return the built entry chunk and its stylesheets, relative to ``js/``.

    Vite writes a manifest describing the content-hashed output of the entry in
    ``ts/App.tsx``. The result is cached against the manifest's mtime: every
    rebuild changes the content hash, so caching it for the process lifetime
    would leave templates pointing at a filename that no longer exists, and the
    resulting 404 reaches the browser as JSON -- which it refuses to load as a
    module. Re-reading costs one stat() per render.
    """
    fallback = ("js/root.js", [])

    manifest_path = _STATIC_JS_DIR / ".vite" / "manifest.json"
    try:
        mtime = manifest_path.stat().st_mtime_ns
    except OSError:
        logger.error("Could not find the frontend build manifest, run `bun run build`!")
        return fallback

    cached = state.cached_bundle_assets
    if cached is not None and cached[0] == mtime:
        return cached[1]

    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError):
        logger.exception("Could not read the frontend build manifest!")
        return fallback

    entry = next((chunk for chunk in manifest.values() if chunk.get("isEntry")), None)
    if entry is None:
        logger.error("Frontend build manifest has no entry chunk!")
        return fallback

    assets = (f"js/{entry['file']}", [f"js/{css}" for css in entry.get("css", [])])
    state.cached_bundle_assets = (mtime, assets)
    return assets


def _make_url_for(state: "TsundokuAppState") -> Callable[..., str]:
    def url_for(name: str, **params: str) -> str:
        if name == "ux.static":
            filename = params["filename"]
            # Rewrite the logical entry name to its content-hashed build output.
            if filename == "js/root.js":
                filename, _css = _load_bundle_assets(state)

            return f"{STATIC_URL_PATH}/{filename}"

        return _NAMED_ROUTES[name]

    return url_for


def static_url(filename: str) -> str:
    """Build a static asset URL outside of a request/template context."""
    return f"{STATIC_URL_PATH}/{filename}"


def render(
    state: "TsundokuAppState",
    request: Request,
    template_name: str,
    **context: object,
) -> HTMLResponse:
    """Render ``template_name`` with Tsundoku's shared template context."""
    fluent = state.get_fluent()

    _js, css = _load_bundle_assets(state)

    full_context: dict[str, object] = {
        "url_for": _make_url_for(state),
        "bundle_css": [f"{STATIC_URL_PATH}/{filename}" for filename in css],
        "get_flashed_messages": lambda with_categories=False: get_flashed_messages(request, with_categories),
        "_": fluent.format_value,
        "LOCALE": state.flags.LOCALE,
        "stats": {"version": version},
        "docker": state.flags.IS_DOCKER,
        "update_info": state.flags.UPDATE_INFO,
        **context,
    }

    return _templates.TemplateResponse(request, template_name, full_context)
