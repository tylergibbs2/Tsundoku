import httpx
import pytest_asyncio

from tests.mock import MockTsundokuAppState, UserType


@pytest_asyncio.fixture(name="client")
async def client_fixture(app: MockTsundokuAppState) -> httpx.AsyncClient:
    """A logged-in client with full read/write permissions."""
    return await app.test_client(user_type=UserType.REGULAR)


@pytest_asyncio.fixture(name="readonly_client")
async def readonly_client_fixture(app: MockTsundokuAppState) -> httpx.AsyncClient:
    """A logged-in client whose user carries the readonly flag.

    Only one client fixture may be used per test: each one creates the single
    ``user`` row, so requesting two collides on the username unique constraint.
    """
    return await app.test_client(user_type=UserType.READONLY)


@pytest_asyncio.fixture(name="anon_client")
async def anon_client_fixture(app: MockTsundokuAppState) -> httpx.AsyncClient:
    """A client with no credentials at all."""
    return await app.test_client(user_type=None)
