from typing import List, Optional

from quart import request, views
from quart import current_app as app

from .response import APIResponse
from tsundoku.webhooks import WebhookBase


class WebhookBaseAPI(views.MethodView):
    async def get(self, base_id: Optional[int]=None) -> List[dict]:
        """
        Retrieve all WebhookBases.

        Parameters
        ----------
        base_id: Optional[int]
            The specific WebhookBase to retrieve.

        Returns
        -------
        List[dict]
            A list of results.
        """
        if not base_id:
            return APIResponse(
                result=[base.to_dict() for base in await WebhookBase.all(app)]
            )
        else:
            base = await WebhookBase.from_id(base_id)
            if base:
                return APIResponse(
                    result=[base.to_dict()]
                )
            else:
                return APIResponse(
                    status=404,
                    error="BaseWebhook with specified ID does not exist."
                )


    async def post(self) -> dict:
        """
        Adds a new webhook base.

        Valid WebhookBase Services:
        dicord, slack, custom

        Returns
        -------
        dict
            The new webhook.
        """
        wh_services = ("discord", "slack", "custom")
        await request.get_data()
        arguments = await request.form

        name = arguments.get("name")
        service = arguments.get("service")
        url = arguments.get("url")
        content_fmt = arguments.get("content_fmt")

        if service not in wh_services:
            return APIResponse(status=400, error="Invalid webhook service.")
        elif not url:
            return APIResponse(status=400, error="Invalid webhook URL.")
        elif not name:
            return APIResponse(status=400, error="Invalid webhook name.")
        elif content_fmt == "":
            content_fmt = None

        base = await WebhookBase.new(
            app,
            name,
            service,
            url,
            content_fmt
        )

        if base:
            return APIResponse(
                result=base.to_dict()
            )
        else:
            return APIResponse(
                status=500,
                error="The server failed to create the new WebhookBase."
            )


    async def put(self, base_id: int) -> dict:
        """
        Updates a specific webhook base.

        Parameters
        ----------
        base_id:
            The ID of the webhook base.

        Returns
        -------
        The updated webhook base.
        """
        wh_services = ("discord", "slack", "custom")
        await request.get_data()
        arguments = await request.form

        name = arguments.get("name")
        service = arguments.get("service")
        url = arguments.get("url")
        content_fmt = arguments.get("content_fmt")

        base = await WebhookBase.from_id(app, base_id)

        if not base:
            return APIResponse(status=404, error="WebhookBase with specified ID does not exist.")
        elif service not in wh_services:
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

        await base.save()

        return APIResponse(
            result=base.to_dict()
        )


    async def delete(self, base_id: int) -> Optional[dict]:
        """
        Deletes a single webhook base.

        Parameters
        ----------
        base_id: int
            The ID of the webhook base.

        Returns
        -------
        Optional[dict]
            If the item was deleted, returns
            the item.
        """
        base = await WebhookBase.from_id(app, base_id)
        if not base:
            return APIResponse(
                status=404,
                error="WebhookBase with specified ID does not exist."
            )

        deleted = await base.delete()

        if deleted:
            return APIResponse(
                result=base.to_dict()
            )
        else:
            return APIResponse(
                status=500,
                error="The server encountered an error deleting the specified WebhookBase."
            )
