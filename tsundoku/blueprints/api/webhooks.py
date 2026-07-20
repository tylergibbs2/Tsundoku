from __future__ import annotations

from fastapi import APIRouter, status

from tsundoku.auth import StateDep
from tsundoku.constants import VALID_TRIGGERS
from tsundoku.webhooks import Webhook

from .response import APIError, Success
from .schemas import WebhookUpdate

router = APIRouter()


@router.get("/shows/{show_id}/webhooks")
async def get_show_webhooks(state: StateDep, show_id: int) -> Success[list[Webhook]]:
    return Success(result=await Webhook.from_show_id(state, show_id))


@router.put("/shows/{show_id}/webhooks/{base_id}")
async def update_show_webhook(state: StateDep, show_id: int, base_id: int, body: WebhookUpdate) -> Success[Webhook]:
    triggers = body.triggers.split(",")
    if len(triggers) == 1 and not triggers[0]:
        triggers = []

    wh = await Webhook.from_composite(state, show_id, base_id)

    if not wh:
        raise APIError(status.HTTP_404_NOT_FOUND, "Webhook with specified ID does not exist.")
    if any(t not in VALID_TRIGGERS for t in triggers):
        raise APIError(status.HTTP_400_BAD_REQUEST, "Invalid webhook triggers.")

    all_triggers = await wh.get_triggers()
    for trigger in all_triggers:
        if trigger not in triggers:
            await wh.remove_trigger(trigger)

    for trigger in triggers:
        await wh.add_trigger(trigger)

    return Success(result=wh)
