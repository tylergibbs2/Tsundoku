import json
from typing import List, Optional

from quart import abort, Response, request, views
from quart import current_app as app
from quart_auth import current_user


async def get_webhook_record(wh_id: int=None, show_id: int=None) -> List[dict]:
    """
    Retrieve all webhooks or a specific webhook
    for a specified show.

    Only one of the parameters can be specified at a time.

    Parameters
    ----------
    wh_id: Optional[int]
        The ID of the webhook to retrieve.
    show_id: Optional[int]
        The ID of the show to retrieve
        webhooks from.

    Returns
    -------
    List[Optional[dict]]
         A list of results.
    """
    if show_id is not None:
        async with app.db_pool.acquire() as con:
            webhooks = await con.fetch("""
                SELECT
                    wh_service,
                    wh_url,
                    content_fmt
                FROM webhook WHERE show_id=$1;
            """, show_id)
            webhooks = [dict(record) for record in webhooks]

            for wh in webhooks:
                triggers = await con.fetch("""
                    SELECT
                        trigger
                    FROM wh_trigger
                    WHERE wh_id=$1;
                """, wh["id"])
                wh["triggers"] = [t["trigger"] for t in triggers]

        return webhooks
    elif wh_id is not None:
        async with app.db_pool.acquire() as con:
            webhook = await con.fetchrow("""
                SELECT
                    wh_service,
                    wh_url,
                    content_fmt
                FROM
                    webhook
                WHERE id=$1;
            """, wh_id)
            webhook = dict(webhook)
            if webhook:
                triggers = await con.fetch("""
                    SELECT
                        trigger
                    FROM wh_trigger
                    WHERE wh_id=$1;
                """, webhook["id"])
                webhook["triggers"] = [t["trigger"] for t in triggers]

            return [webhook]


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
            return json.dumps(await get_webhook_record(show_id=show_id))
        else:
            return json.dumps(await get_webhook_record(wh_id=wh_id))


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

            wh_id = await con.fetchval("""
                INSERT INTO webhook (show_id, wh_service, wh_url)
                VALUES
                ($1, $2, $3);
            """, show_id, service, url)

        webhook = await get_webhook_record(wh_id=wh_id)

        # We could technically avoid doing this
        # and attempt to send the first result,
        # but in case the item isn't created in the
        # DB for some reason, don't error.

        if webhook:
            return json.dumps(webhook[0])
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
        wh = await get_webhook_record(wh_id=wh_id)

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

        wh = wh[0]
        async with app.db_pool.acquire() as con:
            await con.execute("""
                DELETE FROM
                    wh_trigger
                WHERE wh_id=$1;
            """, wh_id)
            for trigger in triggers:
                await con.execute("""
                    INSERT INTO wh_trigger (wh_id, trigger)
                    VALUES
                    ($1, $2);
                """, wh_id, trigger)

            await con.execute("""
                UPDATE webhook
                SET
                    wh_service=$1,
                    wh_url=$2,
                    content_fmt=$3
                WHERE id=$4;
            """, service, url, content_fmt, wh_id)

        return json.dumps(await get_webhook_record(wh_id=wh_id)[0])


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

        async with app.db_pool.acquire() as con:
            deleted = await con.fetchval("""
                DELETE FROM
                    show_entry
                WHERE id=$1
                RETURNING id;
            """, wh_id)

            if deleted:
                return json.dumps(await get_webhook_record(wh_id=deleted))
            else:
                return json.dumps([])
