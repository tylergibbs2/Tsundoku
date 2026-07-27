from collections.abc import Iterator
import json
import re

import pytest

from tests.mock import MockTsundokuAppState, UserType
from tsundoku.templating import _STATIC_JS_DIR, VITE_DEV_ORIGIN

MANIFEST = _STATIC_JS_DIR / ".vite" / "manifest.json"

_JS_SRC = re.compile(r'src="(/ux/static/js/root-[^"]+\.js)"')
_CSS_HREF = re.compile(r'href="(/ux/static/js/root-[^"]+\.css)"')

requires_build = pytest.mark.skipif(not MANIFEST.exists(), reason="frontend not built; run `bun run build`")


@pytest.fixture(name="restore_manifest")
def _restore_manifest() -> Iterator[None]:
    """Put the real manifest back after a test rewrites it."""
    original = MANIFEST.read_text()
    try:
        yield
    finally:
        MANIFEST.write_text(original)


def test_manifest_path_is_absolute() -> None:
    """The manifest must resolve regardless of the server's working directory."""
    assert _STATIC_JS_DIR.is_absolute()


@requires_build
async def test_index_references_built_assets(app: MockTsundokuAppState) -> None:
    client = await app.test_client(user_type=UserType.REGULAR)
    html = (await client.get("/")).text

    js = _JS_SRC.search(html)
    css = _CSS_HREF.search(html)
    assert js is not None, "index.html has no bundle script tag"
    assert css is not None, "base.html has no bundle stylesheet link"

    # Both must actually be served -- a missing file 404s as JSON, which the
    # browser then refuses to load as a module.
    for url in (js.group(1), css.group(1)):
        response = await client.get(url)
        assert response.status_code == 200, f"{url} -> {response.status_code}"

    assert "javascript" in (await client.get(js.group(1))).headers["content-type"]


@requires_build
async def test_bundled_css_has_no_unresolved_sass_variables(app: MockTsundokuAppState) -> None:
    """Guard against shipping a stylesheet that leaked Sass variables.

    bulma-extensions publishes bulma-switch/dist/css with `$switch-*` intact,
    so the paddle compiled to `width: calc($switch-height - ...)` -- invalid,
    silently dropped by the browser, and the switch rendered with no knob.
    """
    client = await app.test_client(user_type=UserType.REGULAR)
    href = _CSS_HREF.search((await client.get("/")).text)
    assert href is not None

    css = (await client.get(href.group(1))).text
    leaked = sorted(set(re.findall(r"\$[a-zA-Z][\w-]*", css)))
    assert not leaked, f"unresolved Sass variables in bundled CSS: {leaked[:10]}"

    # The switch paddle in particular must have real dimensions.
    paddle = re.search(r"\.switch\[type=checkbox\]\+label:{1,2}after[^{}]*\{([^{}]*)\}", css)
    assert paddle is not None, "switch paddle rule missing from bundle"
    assert re.search(r"width:\s*[\d.]", paddle.group(1)), paddle.group(1)


@requires_build
async def test_rebuild_is_picked_up_without_restart(app: MockTsundokuAppState, restore_manifest: None) -> None:
    """A rebuild changes every content hash; templates must follow it.

    Caching the resolved names for the process lifetime left pages pointing at
    a filename that no longer existed after any rebuild.
    """
    client = await app.test_client(user_type=UserType.REGULAR)

    before = _JS_SRC.search((await client.get("/")).text)
    assert before is not None

    # Unchanged manifest: the cached value is reused.
    assert _JS_SRC.search((await client.get("/")).text) is not None

    manifest = json.loads(MANIFEST.read_text())
    entry_key = next(iter(manifest))
    manifest[entry_key]["file"] = "root-rebuilt.js"
    manifest[entry_key]["css"] = ["root-rebuilt.css"]
    MANIFEST.write_text(json.dumps(manifest))

    html = (await client.get("/")).text
    js = _JS_SRC.search(html)
    css = _CSS_HREF.search(html)
    assert js is not None
    assert js.group(1).endswith("root-rebuilt.js")
    assert css is not None
    assert css.group(1).endswith("root-rebuilt.css")


async def test_debug_serves_from_vite_dev_server(app: MockTsundokuAppState) -> None:
    """IS_DEBUG swaps the built bundle for the Vite dev server.

    The react-refresh preamble must precede the client, and no built asset may
    be referenced -- the dev server compiles on demand and injects its own CSS.
    """
    previous = app.flags.IS_DEBUG
    app.flags.IS_DEBUG = True
    try:
        client = await app.test_client(user_type=UserType.REGULAR)
        html = (await client.get("/")).text
    finally:
        app.flags.IS_DEBUG = previous

    assert f"{VITE_DEV_ORIGIN}/@react-refresh" in html
    assert f"{VITE_DEV_ORIGIN}/@vite/client" in html
    assert f"{VITE_DEV_ORIGIN}/tsundoku/blueprints/ux/static/ts/App.tsx" in html

    assert html.index("@react-refresh") < html.index("/@vite/client")
    assert _JS_SRC.search(html) is None
    assert _CSS_HREF.search(html) is None


@requires_build
async def test_without_debug_serves_the_built_bundle(app: MockTsundokuAppState) -> None:
    previous = app.flags.IS_DEBUG
    app.flags.IS_DEBUG = False
    try:
        client = await app.test_client(user_type=UserType.REGULAR)
        html = (await client.get("/")).text
    finally:
        app.flags.IS_DEBUG = previous

    assert _JS_SRC.search(html) is not None
    assert _CSS_HREF.search(html) is not None
    assert VITE_DEV_ORIGIN not in html
