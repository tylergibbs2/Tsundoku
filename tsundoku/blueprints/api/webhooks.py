import json
from typing import List, Optional

from quart import abort, Response, request, views
from quart import current_app as app
from quart_auth import current_user
from tsundoku import webhooks

from tsundoku.webhooks import Webhook, webhook


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
        if not await current_user.is_authenticated:
            return abort(401, "You are not authorized to access this resource.")

        if wh_id is None:
            webhooks = [wh.to_dict() for wh in await Webhook.from_show_id(show_id)]
            return json.dumps(webhooks)
        else:
            webhook = await Webhook.from_wh_id(wh_id)
            return json.dumps(webhook.to_dict())


    async def post(self, show_id: int, entry_id: int=None) -> dict:
        """
        Adds a new webhook.

        Valid Webhook Services:
        dicord, slack, custom

        Parameters
        ----------
        wh_service: str
            The service the webhook posts to.
        wh_url: str
            The URL the webhook posts to.
        content_fmt: str
            The text data that the webhook sends.

        Returns
        -------
        dict
            The new webhook.
        """
        if not await current_user.is_authenticated:
            return abort(401, "You are not authorized to access this resource.")

        wh_services = ("discord", "slack", "custom")
        await request.get_data()
        arguments = await request.form

        service = arguments.get("service")
        url = arguments.get("url")

        if service not in wh_services:
            response = {"error": "invalid webhook service"}
            return Response(json.dumps(response), status=400)
        elif not url:
            response = {"error": "invalid webhook url"}
            return Response(json.dumps(response), status=400)

        async with app.db_pool.acquire() as con:
            show_id = await con.fetchval("""
                SELECT
                    id
                FROM
                    shows
                WHERE id=$1;
            """, show_id)
            if not show_id:
                response = {"error": "invalid show id"}
                return Response(json.dumps(response), status=400)

        webhook = await Webhook.new(
            show_id,
            service,
            url,
            None
        )

        if webhook:
            return json.dumps(webhook.to_dict())
        else:
            return "{}"


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
        if not await current_user.is_authenticated:
            return abort(401, "You are not authorized to access this resource.")

        wh_services = ("discord", "slack", "custom")
        valid_triggers = ("downloading", "downloaded", "renamed", "moved", "completed")
        await request.get_data()
        arguments = await request.form

        service = arguments.get("service")
        url = arguments.get("url")
        triggers = arguments.getlist("triggers")
        content_fmt = arguments.get("content_fmt")

        triggers = triggers.split(",")
        wh = await Webhook.from_wh_id(wh_id)

        if not wh:
            response = {"error": "invalid webhook"}
            return Response(json.dumps(response), status=400)
        elif service not in wh_services:
            response = {"error": "invalid webhook service"}
            return Response(json.dumps(response), status=400)
        elif not url:
            response = {"error": "invalid webhook url"}
            return Response(json.dumps(response), status=400)
        elif not all(t in valid_triggers for t in triggers):
            response = {"error": "invalid triggers"}
            return Response(json.dumps(response), status=400)
        elif not content_fmt:
            response = {"error": "invalid content format"}
            return Response(json.dumps(response), status=400)

        wh.service = service
        wh.url = url
        wh.content_fmt = content_fmt

        await wh.save()

        all_triggers = await wh.get_triggers()
        for trigger in all_triggers:
            if trigger not in triggers:
                await wh.remove_trigger(trigger)

        for trigger in triggers:
            await wh.add_trigger(trigger)

        return json.dumps(wh.to_dict())


    async def delete(self, show_id: int, wh_id: int) -> Optional[dict]:
        """
        Deletes a single webhook from a show.

        Parameters
        ----------
        show_id: int
            The ID of the show.
            Not necessary for this operation.
        wh_id: int
            The ID of the webhook.

        Returns
        -------
        Optional[dict]
            If the item was deleted, returns
            the item.
        """
        if not await current_user.is_authenticated:
            return abort(401, "You are not authorized to access this resource.")

        wh = await Webhook.from_wh_id(wh_id)
        deleted = await wh.delete()

        if deleted:
            return json.dumps(wh.to_dict())
        else:
            return json.dumps([])
