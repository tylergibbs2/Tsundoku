from __future__ import annotations

import logging

from pytest import LogCaptureFixture

from tests.mock import MockTsundokuApp, UserType


async def test_unauthorized_index(app: MockTsundokuApp, caplog: LogCaptureFixture):
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=None)
    response = await client.get("/")
    assert response.status_code == 302


async def test_authorized_index_regular(
    app: MockTsundokuApp, caplog: LogCaptureFixture
):
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.REGULAR)
    response = await client.get("/")
    assert response.status_code == 200


async def test_authorized_index_readonly(
    app: MockTsundokuApp, caplog: LogCaptureFixture
):
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.READONLY)
    response = await client.get("/")
    assert response.status_code == 200
