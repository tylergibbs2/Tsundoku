from __future__ import annotations

from fastapi import APIRouter, status

from tsundoku.auth import ApiUserDep, StateDep
from tsundoku.constants import VALID_SERVICES, VALID_TRIGGERS
from tsundoku.webhooks import WebhookBase

from .response import APIError, Success
from .schemas import WebhookBaseCreate, WebhookBaseUpdate

router = APIRouter()

_CREATE_SERVICES = ("discord", "slack", "custom")
_MASKED_URL = "********"


def _mask(base: WebhookBase, *, readonly: bool) -> WebhookBase:
    """Hide the webhook URL from readonly users."""
    if not readonly:
        return base
    return base.model_copy(update={"url": _MASKED_URL})


def _parse_triggers(raw: str) -> list[str]:
    triggers = raw.split(",")
    if len(triggers) == 1 and not triggers[0]:
        return []
    return triggers


@router.get("/webhooks")
async def get_webhook_bases(state: StateDep, user: ApiUserDep) -> Success[list[WebhookBase]]:
    bases = [_mask(base, readonly=user.readonly) for base in await WebhookBase.all(state)]
    return Success(result=bases)


@router.get("/webhooks/{base_id}")
async def get_webhook_base(state: StateDep, user: ApiUserDep, base_id: int) -> Success[list[WebhookBase]]:
    base = await WebhookBase.from_id(state, base_id)
    if base:
        return Success(result=[_mask(base, readonly=user.readonly)])

    raise APIError(status.HTTP_404_NOT_FOUND, "BaseWebhook with specified ID does not exist.")


@router.post("/webhooks", status_code=status.HTTP_201_CREATED)
async def create_webhook_base(state: StateDep, body: WebhookBaseCreate) -> Success[WebhookBase]:
    triggers = _parse_triggers(body.default_triggers)

    if body.service not in _CREATE_SERVICES:
        raise APIError(status.HTTP_400_BAD_REQUEST, "Invalid webhook service.")
    if not body.url:
        raise APIError(status.HTTP_400_BAD_REQUEST, "Invalid webhook URL.")
    if not body.name:
        raise APIError(status.HTTP_400_BAD_REQUEST, "Invalid webhook name.")
    if any(t not in VALID_TRIGGERS for t in triggers):
        raise APIError(status.HTTP_400_BAD_REQUEST, "Invalid webhook triggers.")

    base = await WebhookBase.new(state, body.name, body.service, body.url, body.content_fmt or None, triggers)

    if base:
        return Success(status=status.HTTP_201_CREATED, result=base)
    raise APIError(status.HTTP_500_INTERNAL_SERVER_ERROR, "The server failed to create the new WebhookBase.")


@router.put("/webhooks/{base_id}")
async def update_webhook_base(state: StateDep, base_id: int, body: WebhookBaseUpdate) -> Success[WebhookBase]:
    base = await WebhookBase.from_id(state, base_id)

    if not base:
        raise APIError(status.HTTP_404_NOT_FOUND, "WebhookBase with specified ID does not exist.")
    if body.service not in VALID_SERVICES:
        raise APIError(status.HTTP_400_BAD_REQUEST, "Invalid webhook service.")
    if not body.url:
        raise APIError(status.HTTP_400_BAD_REQUEST, "Invalid webhook URL.")
    if not body.content_fmt:
        raise APIError(status.HTTP_400_BAD_REQUEST, "Invalid content format.")
    if not body.name:
        raise APIError(status.HTTP_400_BAD_REQUEST, "Invalid name.")

    base.name = body.name
    base.service = body.service
    base.url = body.url
    base.content_fmt = body.content_fmt

    triggers = _parse_triggers(body.default_triggers)
    if any(t not in VALID_TRIGGERS for t in triggers):
        raise APIError(status.HTTP_400_BAD_REQUEST, "Invalid webhook triggers.")

    all_triggers = await base.get_default_triggers()
    for trigger in all_triggers:
        if trigger not in triggers:
            await base.remove_default_trigger(trigger)

    for trigger in triggers:
        await base.add_default_trigger(trigger)

    await base.save()

    return Success(result=base)


@router.delete("/webhooks/{base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_base(state: StateDep, base_id: int) -> None:
    base = await WebhookBase.from_id(state, base_id)
    if not base:
        raise APIError(status.HTTP_404_NOT_FOUND, "WebhookBase with specified ID does not exist.")

    await base.delete()
