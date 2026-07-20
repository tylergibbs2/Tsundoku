from __future__ import annotations

STATIC_URL_PATH = "/ux/static"


def static_url(filename: str) -> str:
    """Build a URL for a static asset served under the UX static mount."""
    return f"{STATIC_URL_PATH}/{filename}"
