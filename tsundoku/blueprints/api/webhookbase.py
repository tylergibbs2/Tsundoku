from typing import List, Optional

from quart import request, views
from quart import current_app as app

from .response import APIResponse
from tsundoku.webhooks import WebhookBase


class WebhookBaseAPI(views.MethodView):
    def _doc_get_0(self) -> None:
        """
        Retrieves all webhooks.

        .. :quickref: Webhooks; Retrieve all webhooks.

        :status 200: webhooks found

        :returns: List[:class:`dict`]
        """

    def _doc_get_1(self) -> None:
        """
        Retrieves a single webhook based on a passed ID.

        .. :quickref: Webhooks; Retrieve a webhook.

        :status 200: webhook found
        :status 404: webhook with passed id not found

        :returns: :class:`dict`
        """

    async def get(self, base_id: Optional[int]=None) -> APIResponse:
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

        base = await WebhookBase.from_id(base_id)
        if base:
            return APIResponse(
                result=[base.to_dict()]
            )

        return APIResponse(
            status=404,
            error="BaseWebhook with specified ID does not exist."
        )


    async def post(self) -> APIResponse:
        """
        Adds a new base webhook.

        .. :quickref: Webhooks; Add a webhook.

        :status 200: webhook added successfully
        :status 400: invalid parameters
        :status 500: unexpected server error

        :form string service: the webhook's service (:code:`discord` or :code:`slack`)
        :form string url: the webhook's post url
        :form string name: the display name of the webhook

        :returns: :class:`dict`
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


    async def put(self, base_id: int) -> APIResponse:
        """
        Updates the webhook with the supplied ID.

        .. :quickref: Webhooks; Update a webhook.

        :status 200: webhook updated successfully
        :status 400: invalid parameters
        :status 404: webhook with passed if not found

        :form string service: the webhook's service (:code:`discord` or :code:`slack`)
        :form string url: the webhook's post url
        :form string name: the display name of the webhook

        :returns: :class:`dict`
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


    async def delete(self, base_id: int) -> APIResponse:
        """
        Deletes a single webhook based on a supplied ID.

        .. :quickref: Webhooks; Delete a webhook.

        :status 200: webhook successfully deleted
        :status 404: webhook with passed id not found
        :status 500: unexpected server error

        :returns: :class:`dict`
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
