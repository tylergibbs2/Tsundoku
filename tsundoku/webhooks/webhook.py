from __future__ import annotations
import logging
from typing import List, Optional

import quart


logger = logging.getLogger("tsundoku")


class ExprDict(dict):
    def __missing__(self, value):
        return value

VALID_SERVICES = ("discord", "slack", "custom")
VALID_TRIGGERS = ("downloading", "downloaded", "renamed", "moved", "completed")


class WebhookBase:
    _app: quart.Quart

    base_id: int
    name: str
    service: str
    url: str
    content_fmt: str

    valid: Optional[bool]

    def to_dict(self) -> dict:
        """
        Return the WebhookBase object as a dict.

        Returns
        -------
        dict
            The dict.
        """
        return {
            "base_id": self.base_id,
            "name": self.name,
            "service": self.service,
            "url": self.url,
            "content_fmt": self.content_fmt,
            "valid": self.valid
        }

    @classmethod
    async def new(cls, app: quart.Quart, name: str, service: str, url: str, content_fmt: Optional[str]=None) -> Optional[WebhookBase]:
        """
        Adds a new WebhookBase to the database and
        returns an instance.

        Parameters
        ----------
        app: quart.Quart:
            The app.
        name: str
            The name of the WebhookBase.
        service: str
            The service.
        url: str
            The POST url.
        content_fmt: Optional[str]
            The content format string.

        Returns
        -------
        Optional[WebhookBase]
            The new WebhookBase.
        """
        if service not in VALID_SERVICES:
            return

        args = (name, service, url)
        if content_fmt:
            query = """
                INSERT INTO
                    webhook_base
                    (name, base_service, base_url, content_fmt)
                VALUES
                    ($1, $2, $3, $4)
                RETURNING id, content_fmt;
            """
            args += (content_fmt,)
        else:
            query = """
                INSERT INTO
                    webhook_base
                    (name, base_service, base_url)
                VALUES
                    ($1, $2, $3)
                RETURNING id, content_fmt;
            """

        async with app.db_pool.acquire() as con:
            new_base = await con.fetchrow(query, *args)

        if not new_base:
            return

        async with app.db_pool.acquire() as con:
            await con.execute("""
                INSERT INTO
                    webhook
                    (show_id, base)
                SELECT id, ($1) FROM shows
                ON CONFLICT DO NOTHING;
            """, new_base["id"])

        instance = cls()

        instance._app = app

        instance.base_id = new_base["id"]
        instance.name = name
        instance.service = service
        instance.url = url
        instance.content_fmt = new_base["content_fmt"]
        instance.valid = await instance.is_valid()

        return instance

    @classmethod
    async def from_id(cls, app: quart.Quart, base_id: int, with_validity: bool=True) -> Optional[WebhookBase]:
        """
        Returns a WebhookBase object from a webhook base ID.

        Parameters
        ----------
        app: quart.Quart
            The app.
        base_id: int
            The WebhookBase's ID.
        with_validity: bool
            Whether or not to grab the WebhookBase valid state.

        Returns
        -------
        Optional[WebhookBase]
            The requested webhook base.
        """
        async with app.db_pool.acquire() as con:
            base = await con.fetchrow("""
                SELECT
                    id,
                    name,
                    base_service,
                    base_url,
                    content_fmt
                FROM
                    webhook_base
                WHERE
                    id=$1;
            """, base_id)

        if not base:
            return

        async with app.db_pool.acquire() as con:
            await con.execute("""
                INSERT INTO
                    webhook
                    (show_id, base)
                SELECT id, ($1) FROM shows
                ON CONFLICT DO NOTHING;
            """, base_id)

        instance = cls()

        instance._app = app

        instance.base_id = base["id"]
        instance.name = base["name"]
        instance.service = base["base_service"]
        instance.url = base["base_url"]
        instance.content_fmt = base["content_fmt"]

        if with_validity:
            instance.valid = await instance.is_valid()
        else:
            instance.valid = None

        return instance

    @classmethod
    async def all(cls, app: quart.Quart) -> List[WebhookBase]:
        """
        Returns all WebhookBase rows from
        the database.

        Parameters
        ----------
        app: quart.Quart
            The app.

        Returns
        -------
        List[WebhookBase]
            All rows.
        """
        async with app.db_pool.acquire() as con:
            ids = await con.fetch("""
                SELECT
                    id
                FROM
                    webhook_base
                ORDER BY
                    id ASC;
            """)

        instances = []
        for id_ in ids:
            instances.append(await WebhookBase.from_id(app, id_["id"]))

        return instances

    async def save(self) -> bool:
        """
        Saves the attributes of the object
        to the database.

        Returns
        -------
        bool:
            Whether it was saved or not.
        """
        if self.service not in VALID_SERVICES:
            return False
        elif not self.content_fmt:
            return False

        async with self._app.db_pool.acquire() as con:
            updated = await con.fetchval("""
                UPDATE
                    webhook_base
                SET
                    name=$1,
                    base_service=$2,
                    base_url=$3,
                    content_fmt=$4
                WHERE
                    id=$5
                RETURNING content_fmt;
            """, self.name, self.service, self.url, self.content_fmt, self.base_id)

        return bool(updated)

    async def delete(self) -> bool:
        """
        Deletes a WebhookBase from the database.

        Returns
        -------
        bool:
            Whether the webhook base was deleted or not.
        """
        async with self._app.db_pool.acquire() as con:
            deleted = await con.fetchval("""
                DELETE FROM
                    webhook_base
                WHERE
                    id=$1
                RETURNING content_fmt;
            """, self.base_id)

        return bool(deleted)

    async def is_valid(self) -> bool:
        """
        Checks if the webhook URL is valid.
        """
        if self.service == "slack":
            try:
                resp = await self._app.session.post(self.url, json={"text": ""})
            except Exception as e:
                return False
            text = await resp.text()
            return text == "no_text"
        else:
            try:
                resp = await self._app.session.head(self.url)
            except Exception as e:
                return False
            return resp.status == 200


class Webhook:
    _app: quart.Quart

    show_id: int
    base: WebhookBase

    def to_dict(self) -> dict:
        """
        Return the Webhook object as a dict.

        Returns
        -------
        dict
            The dict.
        """
        return {
            "show_id": self.show_id,
            "base": self.base.to_dict()
        }

    @classmethod
    async def from_show_id(cls, app: quart.Quart, show_id: int) -> List[Webhook]:
        """
        Returns all webhooks for a specified show ID.

        Parameters
        ----------
        app: quart.Quart
            The app.
        show_id: int
            The show's ID.

        Returns
        -------
        List[Webhook]
            All found webhooks.
        """
        async with app.db_pool.acquire() as con:
            webhooks = await con.fetch("""
                SELECT
                    id, base
                FROM
                    webhook
                WHERE
                    show_id=$1
                ORDER BY
                    id ASC;
            """, show_id)

        instances = []

        for wh in webhooks:
            base = await WebhookBase.from_id(app, wh["base"], with_validity=False)
            if not base:
                continue

            instance = cls()

            instance._app = app

            instance.wh_id = wh["id"]
            instance.show_id = show_id
            instance.base = base

            instances.append(instance)

        return instances

    @classmethod
    async def from_composite(cls, app: quart.Quart, show_id: int, base_id: int) -> Optional[Webhook]:
        """
        Returns a webhook from its composite key.

        Parameters
        ----------
        app: quart.Quart
            The app.
        show_id: int
            The show's ID.
        base_id: int
            The webhook's base's ID.

        Returns
        -------
        Optional[Webhook]
            The found webhook.
        """
        async with app.db_pool.acquire() as con:
            webhook = await con.fetchrow("""
                SELECT
                    id, base
                FROM
                    webhook
                WHERE
                    show_id=$1 AND base=$2;
            """, show_id, base_id)

        base = await WebhookBase.from_id(app, webhook["base"], with_validity=False)
        if not base:
            return

        instance = cls()

        instance._app = app

        instance.wh_id = webhook["id"]
        instance.show_id = show_id
        instance.base = base

        return instance

    async def get_triggers(self) -> List[str]:
        """
        Retrieves all triggers for a webhook.

        Returns
        -------
        List[str]
            All valid triggers.
        """
        async with self._app.db_pool.acquire() as con:
            triggers = await con.fetch("""
                SELECT
                    trigger
                FROM
                    webhook_trigger
                WHERE wh_id=$1;
            """, self.wh_id)

        return [r["trigger"] for r in triggers]

    async def add_trigger(self, trigger: str) -> bool:
        """
        Adds a new trigger to a webhook.

        Parameters
        ----------
        trigger: str
            The valid trigger.

        Returns
        -------
        bool
            Whether the webhook was added or not.
        """
        if trigger not in VALID_TRIGGERS:
            return False

        async with self._app.db_pool.acquire() as con:
            exists = await con.fetchval("""
                SELECT
                    trigger
                FROM
                    webhook_trigger
                WHERE wh_id=$1 AND trigger=$2;
            """, self.wh_id, trigger)

            if exists:
                return True

            await con.execute("""
                INSERT INTO
                    webhook_trigger
                    (wh_id, trigger)
                VALUES
                    ($1, $2);
            """, self.wh_id, trigger)

        return True

    async def remove_trigger(self, trigger: str) -> bool:
        """
        Removes a trigger from a webhook.

        Parameters
        ----------
        trigger: str
            The valid trigger.

        Returns
        -------
        bool
            Whether the webhook was deleted or not.
        """
        if trigger not in VALID_TRIGGERS:
            return False

        async with self._app.db_pool.acquire() as con:
            exists = await con.fetchval("""
                SELECT
                    trigger
                FROM
                    webhook_trigger
                WHERE wh_id=$1 AND trigger=$2;
            """, self.wh_id, trigger)

            if not exists:
                return False

            await con.execute("""
                DELETE FROM
                    webhook_trigger
                WHERE wh_id=$1 AND trigger=$2;
            """, self.wh_id, trigger)

        return True

    def generate_discord_embed(self, content: str) -> dict:
        """
        Generates a Discord sendable embed.

        Parameters
        ----------
        content: str
            The content of the webhook.

        Returns
        -------
        A embed that can be sent to Discord.
        """
        embed = {}

        embed["title"] = "Tsundoku Progress Event"
        embed["color"] = 370725
        embed["description"] = content

        return embed

    def generate_slack_blocks(self, content: str) -> List[dict]:
        """
        Generates a Slack Block for the content.

        Parameters
        ----------
        content: str
            The content of the webhook.

        Returns
        -------
        A block that can be sent to Slack.
        """
        title_block = {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Tsundoku Progress Event"
            }
        }

        content_block = {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": content
            }
        }

        return [title_block, content_block]

    async def generate_payload(self, episode: int, event: str) -> dict:
        """
        Generates the complete payload for
        a webhook send.

        Parameters
        ----------
        episode: int
            The episode number.
        event: str
            The event that occurred.

        Returns
        -------
        dict:
            The generated payload.
        """
        async with self._app.db_pool.acquire() as con:
            show_name = await con.fetchval("""
                SELECT
                    title
                FROM
                    shows
                WHERE id=$1;
            """, self.show_id)

        if not show_name:
            return

        payload = {}

        expr = ExprDict(
            name=show_name,
            episode=episode,
            state=event
        )

        content = self.base.content_fmt.format_map(expr)

        if self.base.service == "discord":
            # Discord expects an array
            payload["embeds"] = [self.generate_discord_embed(content)]
        elif self.base.service == "slack":
            payload["blocks"] = self.generate_slack_blocks(content)
        else:
            payload["content"] = content
            payload["text"] = content

        return payload

    async def send(self, episode: int, event: str):
        """
        Posts an event with data to a webhook.

        Parameters
        ----------
        episode: int
            The episode number.
        event: str
            The event that occurred, can be any `show_state`.
        """
        if not self.base.valid:
            return

        logger.debug(f"Webhooks - Generating payload for Webhook with ID {self.wh_id}")
        payload = await self.generate_payload(episode, event)

        if not payload:
            logger.warn(f"Webhooks - Failed to generate a valid payload for Webhook with ID {self.wh_id}")
            return

        logger.debug(f"Webhooks - Payload generated for Webhook with ID {self.wh_id}")

        logger.debug(f"Webhooks - Webhook {self.wh_id} sending payload...")

        try:
            await self._app.session.post(self.base.url, json=payload)
        except Exception as e:
            pass
