import httpx
import pytest

from tests.mock import MockTsundokuAppState

from .envelope import API, error, success

VALID_BASE = {
    "name": "notify",
    "service": "discord",
    "url": "https://discord.test/hook",
    "content_fmt": "{name} - {episode}",
    "default_triggers": "downloading,downloaded",
}


async def create_base(client: httpx.AsyncClient, **overrides: object) -> dict:
    body = {**VALID_BASE, **overrides}
    return success(await client.post(f"{API}/webhooks", json=body), 201)


# ---------------------------------------------------------------------------
# Webhook bases
# ---------------------------------------------------------------------------


async def test_list_webhook_bases_starts_empty(client: httpx.AsyncClient) -> None:
    assert success(await client.get(f"{API}/webhooks")) == []


async def test_create_webhook_base(client: httpx.AsyncClient) -> None:
    result = await create_base(client)

    assert result["name"] == "notify"
    assert result["service"] == "discord"
    assert result["url"] == "https://discord.test/hook"
    assert sorted(result["default_triggers"]) == ["downloaded", "downloading"]


async def test_created_base_appears_in_listing(client: httpx.AsyncClient) -> None:
    created = await create_base(client)

    listed = success(await client.get(f"{API}/webhooks"))

    assert [base["base_id"] for base in listed] == [created["base_id"]]


async def test_get_webhook_base_by_id(client: httpx.AsyncClient) -> None:
    created = await create_base(client)

    # Declares Success[list[WebhookBase]], so a single base is still a list.
    result = success(await client.get(f"{API}/webhooks/{created['base_id']}"))

    assert [base["base_id"] for base in result] == [created["base_id"]]


async def test_get_unknown_webhook_base_is_404(client: httpx.AsyncClient) -> None:
    assert error(await client.get(f"{API}/webhooks/9999"), 404) == "BaseWebhook with specified ID does not exist."


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"service": "telegram"}, "Invalid webhook service."),
        ({"url": ""}, "Invalid webhook URL."),
        ({"name": ""}, "Invalid webhook name."),
        ({"default_triggers": "exploded"}, "Invalid webhook triggers."),
    ],
)
async def test_create_webhook_base_validation(client: httpx.AsyncClient, overrides: dict, message: str) -> None:
    response = await client.post(f"{API}/webhooks", json={**VALID_BASE, **overrides})

    assert error(response, 400) == message


async def test_create_webhook_base_accepts_no_triggers(client: httpx.AsyncClient) -> None:
    result = await create_base(client, default_triggers="")

    assert result["default_triggers"] == []


async def test_update_webhook_base(client: httpx.AsyncClient) -> None:
    created = await create_base(client)

    result = success(
        await client.put(
            f"{API}/webhooks/{created['base_id']}",
            json={**VALID_BASE, "name": "renamed", "service": "slack", "default_triggers": "renamed"},
        )
    )

    assert result["name"] == "renamed"
    assert result["service"] == "slack"
    assert result["default_triggers"] == ["renamed"]


async def test_update_webhook_base_replaces_triggers(client: httpx.AsyncClient) -> None:
    """Triggers are a full replacement, not a union with what was there."""
    created = await create_base(client, default_triggers="downloading,downloaded,renamed")

    result = success(await client.put(f"{API}/webhooks/{created['base_id']}", json={**VALID_BASE, "default_triggers": "moved"}))

    assert result["default_triggers"] == ["moved"]


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"service": "telegram"}, "Invalid webhook service."),
        ({"url": ""}, "Invalid webhook URL."),
        ({"content_fmt": ""}, "Invalid content format."),
        ({"name": ""}, "Invalid name."),
        ({"default_triggers": "exploded"}, "Invalid webhook triggers."),
    ],
)
async def test_update_webhook_base_validation(client: httpx.AsyncClient, overrides: dict, message: str) -> None:
    created = await create_base(client)

    response = await client.put(f"{API}/webhooks/{created['base_id']}", json={**VALID_BASE, **overrides})

    assert error(response, 400) == message


async def test_update_unknown_webhook_base_is_404(client: httpx.AsyncClient) -> None:
    response = await client.put(f"{API}/webhooks/9999", json=VALID_BASE)

    assert error(response, 404) == "WebhookBase with specified ID does not exist."


async def test_delete_webhook_base(client: httpx.AsyncClient) -> None:
    created = await create_base(client)

    response = await client.delete(f"{API}/webhooks/{created['base_id']}")

    assert response.status_code == 204
    assert success(await client.get(f"{API}/webhooks")) == []


async def test_delete_unknown_webhook_base_is_404(client: httpx.AsyncClient) -> None:
    assert error(await client.delete(f"{API}/webhooks/9999"), 404) == "WebhookBase with specified ID does not exist."


# ---------------------------------------------------------------------------
# URL masking
# ---------------------------------------------------------------------------


async def test_readonly_users_never_see_webhook_urls(app: MockTsundokuAppState, readonly_client: httpx.AsyncClient) -> None:
    """A webhook URL is a bearer credential: anyone holding it can post as you."""
    # Seeded directly rather than via POST, which a readonly user cannot do.
    async with app.acquire_db() as con:
        await con.execute(
            "INSERT INTO webhook_base (id, name, base_service, base_url, content_fmt) VALUES (?,?,?,?,?);",
            1,
            "notify",
            "discord",
            "https://discord.test/secret-hook",
            "{name}",
        )

    listed = success(await readonly_client.get(f"{API}/webhooks"))
    assert listed[0]["url"] == "********"

    single = success(await readonly_client.get(f"{API}/webhooks/1"))
    assert single[0]["url"] == "********"


async def test_regular_users_do_see_webhook_urls(client: httpx.AsyncClient) -> None:
    created = await create_base(client)

    assert created["url"] == "https://discord.test/hook"
    assert success(await client.get(f"{API}/webhooks"))[0]["url"] == "https://discord.test/hook"


# ---------------------------------------------------------------------------
# Per-show webhooks
# ---------------------------------------------------------------------------


async def test_show_webhooks_are_created_for_each_base(client: httpx.AsyncClient) -> None:
    """Creating a base links it to every existing show."""
    await create_base(client)

    result = success(await client.get(f"{API}/shows/1/webhooks"))

    assert len(result) == 1
    assert result[0]["show_id"] == 1


async def test_update_show_webhook_triggers(client: httpx.AsyncClient) -> None:
    created = await create_base(client)

    result = success(await client.put(f"{API}/shows/1/webhooks/{created['base_id']}", json={"triggers": "downloading,moved"}))

    assert sorted(result["triggers"]) == ["downloading", "moved"]


async def test_clear_show_webhook_triggers(client: httpx.AsyncClient) -> None:
    created = await create_base(client)
    await client.put(f"{API}/shows/1/webhooks/{created['base_id']}", json={"triggers": "downloading"})

    result = success(await client.put(f"{API}/shows/1/webhooks/{created['base_id']}", json={"triggers": ""}))

    assert result["triggers"] == []


async def test_update_show_webhook_rejects_invalid_trigger(client: httpx.AsyncClient) -> None:
    created = await create_base(client)

    response = await client.put(f"{API}/shows/1/webhooks/{created['base_id']}", json={"triggers": "exploded"})

    assert error(response, 400) == "Invalid webhook triggers."


async def test_update_unknown_show_webhook_is_404(client: httpx.AsyncClient) -> None:
    response = await client.put(f"{API}/shows/1/webhooks/9999", json={"triggers": ""})

    assert error(response, 404) == "Webhook with specified ID does not exist."
