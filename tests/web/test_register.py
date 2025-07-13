import logging

from pytest import LogCaptureFixture

from tests.mock import MockTsundokuApp, UserType


async def test_register_no_user_has_redirect(app: MockTsundokuApp, caplog: LogCaptureFixture):
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=None)
    response = await client.get("/")
    assert response.status_code == 302


async def test_register_no_user_can_access(app: MockTsundokuApp, caplog: LogCaptureFixture):
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=None)
    response = await client.get("/register")
    assert response.status_code == 200


async def test_register_regular_user(app: MockTsundokuApp, caplog: LogCaptureFixture):
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.REGULAR)
    response = await client.get("/register")
    assert response.status_code == 302


async def test_register_readonly_user(app: MockTsundokuApp, caplog: LogCaptureFixture):
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.READONLY)
    response = await client.get("/register")
    assert response.status_code == 403
