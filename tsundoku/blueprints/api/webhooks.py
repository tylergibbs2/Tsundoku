from typing import List

from quart import request, views
from quart import current_app as app

from .response import APIResponse
from tsundoku.webhooks import Webhook


class WebhooksAPI(views.MethodView):
    async def get(self, show_id: int, wh_id: int=None) -> List[dict]:
        """
        Retrieve all webhooks or a specific webhook
        for a specified show.

        Parameters
        ----------
        show_id: int
            The show to retrieve webhooks for.
        wh_id: int
            The specific webhook to retrieve.

        Returns
        -------
        List[dict]
            A list of results.
        """
        if wh_id is None:
            webhooks = [wh.to_dict() for wh in await Webhook.from_show_id(app, show_id)]
            return APIResponse(
                result=webhooks
            )
        else:
            webhook = await Webhook.from_wh_id(app, wh_id)
            return APIResponse(
                result=webhook.to_dict()
            )

    async def put(self, show_id: int, wh_id: int) -> dict:
        """
        Updates a specific webhook.

        Also for adding triggers.

        Parameters
        ----------
        show_id: int
            The ID of the show.
            Not necessary for this operation.
        wh_id: int
            The ID of the webhook.

        Returns
        -------
        The updated webhook.
        """
        valid_triggers = ("downloading", "downloaded", "renamed", "moved", "completed")
        await request.get_data()
        arguments = await request.form

        triggers = arguments.get("triggers")
        triggers = triggers.split(",")

        if len(triggers) == 1 and not triggers[0]:
            triggers = []

        wh = await Webhook.from_wh_id(app, wh_id)

        if not wh:
            return APIResponse(status=404, error="Webhook with specified ID does not exist.")
        elif not all(t in valid_triggers for t in triggers):
            return APIResponse(status=400, error="Invalid webhook triggers.")

        all_triggers = await wh.get_triggers()
        for trigger in all_triggers:
            if trigger not in triggers:
                await wh.remove_trigger(trigger)

        for trigger in triggers:
            await wh.add_trigger(trigger)

        return APIResponse(
            result=wh.to_dict()
        )
