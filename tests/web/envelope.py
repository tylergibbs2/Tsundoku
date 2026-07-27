"""Assertions for the API's standard response envelopes."""

from typing import Any

import httpx

API = "/api/v1"


def success(response: httpx.Response, expected_status: int = 200) -> Any:
    """Assert the standard success envelope and return its ``result``.

    Every API endpoint declares ``Success[T]``, so the body is always
    ``{"status": ..., "result": ...}``. Asserting the shape here means a
    regression in the envelope fails every test rather than going unnoticed.
    """
    assert response.status_code == expected_status, response.text

    body = response.json()
    assert set(body) == {"status", "result"}, f"unexpected envelope keys: {sorted(body)}"
    assert body["status"] == expected_status

    return body["result"]


def error(response: httpx.Response, expected_status: int) -> str:
    """Assert the standard error envelope and return its message."""
    assert response.status_code == expected_status, response.text

    body = response.json()
    assert set(body) == {"status", "error"}, f"unexpected envelope keys: {sorted(body)}"
    assert body["status"] == expected_status

    return body["error"]
