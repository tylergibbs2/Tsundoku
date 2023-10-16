from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp
    from tsundoku.user import User

    app: TsundokuApp
    current_user: User
else:
    from quart import current_app as app
    from quart_auth import current_user

from quart import request, views

from tsundoku.constants import VALID_TRIGGERS, VALID_SERVICES
from tsundoku.webhooks import WebhookBase

from .response import APIResponse


class WebhookBaseAPI(views.MethodView):
    async def get(self, base_id: Optional[int] = None) -> APIResponse:
        hidden_url = await current_user.readonly
        if not base_id:
            return APIResponse(
                result=[
                    base.to_dict(secure=hidden_url)
                    for base in await WebhookBase.all(app)
                ]
            )

        base = await WebhookBase.from_id(app, base_id)
        if base:
            return APIResponse(result=[base.to_dict(secure=hidden_url)])

        return APIResponse(
            status=404, error="BaseWebhook with specified ID does not exist."
        )

    async def post(self) -> APIResponse:
        wh_services = ("discord", "slack", "custom")
        arguments = await request.get_json()

        name = arguments.get("name")
        service = arguments.get("service")
        url = arguments.get("url")
        content_fmt = arguments.get("content_fmt")

        triggers = arguments.get("default_triggers", "")
        triggers = triggers.split(",")
        if len(triggers) == 1 and not triggers[0]:
            triggers = []

        if service not in wh_services:
            return APIResponse(status=400, error="Invalid webhook service.")
        elif not url:
            return APIResponse(status=400, error="Invalid webhook URL.")
        elif not name:
            return APIResponse(status=400, error="Invalid webhook name.")
        elif any(t not in VALID_TRIGGERS for t in triggers):
            return APIResponse(status=400, error="Invalid webhook triggers.")
        elif content_fmt == "":
            content_fmt = None

        base = await WebhookBase.new(app, name, service, url, content_fmt, triggers)

        if base:
            return APIResponse(result=base.to_dict())
        else:
            return APIResponse(
                status=500, error="The server failed to create the new WebhookBase."
            )

    async def put(self, base_id: int) -> APIResponse:
        arguments = await request.get_json()

        name = arguments.get("name")
        service = arguments.get("service")
        url = arguments.get("url")
        content_fmt = arguments.get("content_fmt")

        base = await WebhookBase.from_id(app, base_id)

        if not base:
            return APIResponse(
                status=404, error="WebhookBase with specified ID does not exist."
            )
        elif service not in VALID_SERVICES:
            return APIResponse(status=400, error="Invalid webhook service.")
        elif not url:
            return APIResponse(status=400, error="Invalid webhook URL.")
        elif not content_fmt:
            return APIResponse(status=400, error="Invalid content format.")
        elif not name:
            return APIResponse(status=400, error="Invalid name.")

        base.name = name
        base.service = service
        base.url = url
        base.content_fmt = content_fmt

        triggers = arguments.get("default_triggers", "")
        triggers = triggers.split(",")

        if len(triggers) == 1 and not triggers[0]:
            triggers = []
        elif any(t not in VALID_TRIGGERS for t in triggers):
            return APIResponse(status=400, error="Invalid webhook triggers.")

        all_triggers = await base.get_default_triggers()
        for trigger in all_triggers:
            if trigger not in triggers:
                await base.remove_default_trigger(trigger)

        for trigger in triggers:
            await base.add_default_trigger(trigger)

        await base.save()

        return APIResponse(result=base.to_dict())

    async def delete(self, base_id: int) -> APIResponse:
        base = await WebhookBase.from_id(app, base_id)
        if not base:
            return APIResponse(
                status=404, error="WebhookBase with specified ID does not exist."
            )

        await base.delete()
        return APIResponse(result=base.to_dict())
