import logging

import pytest

from tests.mock import MockTsundokuApp, UserType
from tsundoku.webhooks import WebhookBase


async def test_unauthorized_index(app: MockTsundokuApp, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=None)
    response = await client.get("/")
    assert response.status_code == 302


async def test_unauthorized_shows_list(app: MockTsundokuApp, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=None)
    response = await client.get("/api/v1/shows")
    assert response.status_code == 401


async def test_authorized_index_regular(app: MockTsundokuApp, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.REGULAR)
    response = await client.get("/")
    assert response.status_code == 200


async def test_authorized_shows_list(app: MockTsundokuApp, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.REGULAR)
    response = await client.get("/api/v1/shows")
    assert response.status_code == 200


async def test_authorized_shows_list_pagination(app: MockTsundokuApp, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.REGULAR)
    response = await client.get("/api/v1/shows?page=1&limit=5")
    assert response.status_code == 200

    data = await response.json
    assert "shows" in data["result"]
    assert "pagination" in data["result"]
    assert data["result"]["pagination"]["page"] == 1
    assert data["result"]["pagination"]["limit"] == 5


async def test_authorized_index_readonly(app: MockTsundokuApp, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.READONLY)
    response = await client.get("/")
    assert response.status_code == 200


async def test_authorized_readonly_hidden_webhook_url(app: MockTsundokuApp, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    await WebhookBase.new(app, "My Webhook", "discord", "https://super-secret.com")  # type: ignore

    client = await app.test_client(user_type=UserType.READONLY)
    response = await client.get("/api/v1/webhooks")
    data = await response.json
    assert data["status"] == 200

    webhook = data["result"][0]
    assert all(c == "*" for c in webhook["url"])
