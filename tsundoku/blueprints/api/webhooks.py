from quart import current_app as app
from quart import request, views

from tsundoku.webhooks import Webhook, VALID_TRIGGERS

from .response import APIResponse


class WebhooksAPI(views.MethodView):
    async def get(self, show_id: int) -> APIResponse:
        webhooks = [wh.to_dict() for wh in await Webhook.from_show_id(app, show_id)]
        return APIResponse(result=webhooks)

    async def put(self, show_id: int, base_id: int) -> APIResponse:
        arguments = await request.get_json()

        triggers = arguments.get("triggers")
        triggers = triggers.split(",")

        if len(triggers) == 1 and not triggers[0]:
            triggers = []

        wh = await Webhook.from_composite(app, show_id, base_id)

        if not wh:
            return APIResponse(
                status=404, error="Webhook with specified ID does not exist."
            )
        elif any(t not in VALID_TRIGGERS for t in triggers):
            return APIResponse(status=400, error="Invalid webhook triggers.")

        all_triggers = await wh.get_triggers()
        for trigger in all_triggers:
            if trigger not in triggers:
                await wh.remove_trigger(trigger)

        for trigger in triggers:
            await wh.add_trigger(trigger)

        return APIResponse(result=wh.to_dict())
