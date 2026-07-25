"""Authorization guarantees across the whole API surface.

These tests enumerate routes from the OpenAPI schema rather than a hand-written
list, so a newly added endpoint is covered the moment it exists. A route that
needs to opt out has to do so explicitly below, which makes the exception
visible in review.
"""

import httpx
import pytest

from tests.mock import MockTsundokuAppState

from .envelope import error

MUTATING_METHODS = ("POST", "PUT", "PATCH", "DELETE")

#: Placeholder values for path parameters. The request is expected to be
#: rejected before the handler runs, so these only need to be well-typed.
PATH_PARAM_VALUES = {
    "library_id": "1",
    "show_id": "1",
    "entry_id": "1",
    "base_id": "1",
}


def api_routes(app: MockTsundokuAppState, methods: tuple[str, ...]) -> list[tuple[str, str]]:
    """Every ``(method, concrete path)`` pair the API exposes for ``methods``."""
    paths = app.asgi_app.openapi()["paths"]

    routes: list[tuple[str, str]] = []
    for template, operations in sorted(paths.items()):
        if not template.startswith("/api/v1"):
            continue

        path = template
        for name, value in PATH_PARAM_VALUES.items():
            path = path.replace(f"{{{name}}}", value)

        assert "{" not in path, f"unmapped path parameter in {template}; add it to PATH_PARAM_VALUES"

        routes.extend((method.upper(), path) for method in operations if method.upper() in methods)

    return routes


def test_route_inventory_is_not_empty(app: MockTsundokuAppState) -> None:
    """Guard the guards: a broken enumeration would silently pass everything."""
    assert len(api_routes(app, MUTATING_METHODS)) >= 20
    assert len(api_routes(app, ("GET",))) >= 15


async def test_every_route_rejects_anonymous_requests(app: MockTsundokuAppState, anon_client: httpx.AsyncClient) -> None:
    all_methods = (*MUTATING_METHODS, "GET")

    failures = []
    for method, path in api_routes(app, all_methods):
        response = await anon_client.request(method, path, json={})
        if response.status_code != 401:
            failures.append(f"{method} {path} -> {response.status_code}")

    assert not failures, "routes reachable without authentication:\n" + "\n".join(failures)


async def test_every_mutating_route_rejects_readonly_users(app: MockTsundokuAppState, readonly_client: httpx.AsyncClient) -> None:
    failures = []
    for method, path in api_routes(app, MUTATING_METHODS):
        response = await readonly_client.request(method, path, json={})
        if response.status_code != 403:
            failures.append(f"{method} {path} -> {response.status_code}")

    assert not failures, "mutating routes writable by a readonly user:\n" + "\n".join(failures)


async def test_readonly_rejection_precedes_body_validation(readonly_client: httpx.AsyncClient) -> None:
    """A readonly user gets 403, not 422, even when the body is malformed.

    Validating first would tell an unauthorized caller which fields exist.
    """
    response = await readonly_client.post("/api/v1/libraries", json={"nonsense": True})

    assert error(response, 403) == "You are forbidden from modifying this resource."


async def test_readonly_users_can_still_read(readonly_client: httpx.AsyncClient) -> None:
    result = await readonly_client.get("/api/v1/libraries")

    assert result.status_code == 200


@pytest.mark.parametrize(
    "header",
    ["Basic dXNlcjpwYXNz", "Bearer", "token abc123", "bearer lowercase-scheme"],
)
async def test_malformed_authorization_header_is_rejected(anon_client: httpx.AsyncClient, header: str) -> None:
    response = await anon_client.get("/api/v1/libraries", headers={"Authorization": header})

    assert response.status_code == 401


async def test_unknown_api_key_is_rejected(anon_client: httpx.AsyncClient) -> None:
    response = await anon_client.get("/api/v1/libraries", headers={"Authorization": "Bearer not-a-real-key"})

    assert response.status_code == 401


async def test_api_key_grants_access(app: MockTsundokuAppState, client: httpx.AsyncClient) -> None:
    """The API key issued to a user authenticates without the session cookie."""
    async with app.acquire_db() as con:
        api_key = await con.fetchval("SELECT api_key FROM users LIMIT 1;")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app.asgi_app),
        base_url="http://testserver",
    ) as keyed:
        response = await keyed.get("/api/v1/libraries", headers={"Authorization": f"Bearer {api_key}"})

    assert response.status_code == 200
