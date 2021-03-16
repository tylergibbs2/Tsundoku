from __future__ import annotations

import logging
from typing import Any, List, Optional, Tuple

logger = logging.getLogger("tsundoku")


class ExprDict(dict):
    def __missing__(self, value: str) -> str:
        return value


VALID_SERVICES = ("discord", "slack", "custom")
VALID_TRIGGERS = ("downloading", "downloaded", "renamed", "moved", "completed")


class WebhookBase:
    _app: Any

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
    async def new(cls, app: Any, name: str, service: str, url: str,
                  content_fmt: Optional[str] = None) -> Optional[WebhookBase]:
        """
        Adds a new WebhookBase to the database and
        returns an instance.

        Parameters
        ----------
        app: Any:
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
            return None

        args: Tuple[str, ...] = (name, service, url)
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
            return None

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
    async def from_id(cls, app: Any, base_id: int, with_validity: bool = True) -> Optional[WebhookBase]:
        """
        Returns a WebhookBase object from a webhook base ID.

        Parameters
        ----------
        app: Any
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
            return None

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
    async def all(cls, app: Any) -> List[WebhookBase]:
        """
        Returns all WebhookBase rows from
        the database.

        Parameters
        ----------
        app: Any
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
            wh_base = await WebhookBase.from_id(app, id_["id"])
            if wh_base:
                instances.append(wh_base)

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
            except Exception:
                return False
            text = await resp.text()
            return text == "no_text"
        else:
            try:
                resp = await self._app.session.head(self.url)
            except Exception:
                return False
            return resp.status == 200


class Webhook:
    _app: Any

    show_id: int
    base: WebhookBase
    triggers: List[str]

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
            "base": self.base.to_dict(),
            "triggers": self.triggers
        }

    @classmethod
    async def from_show_id(cls, app: Any, show_id: int, with_validity: bool = False) -> List[Webhook]:
        """
        Returns all webhooks for a specified show ID.

        Parameters
        ----------
        app: Any
            The app.
        show_id: int
            The show's ID.
        with_validity: bool
            Whether to also retrieve the base webhook's validity.

        Returns
        -------
        List[Webhook]
            All found webhooks.
        """
        async with app.db_pool.acquire() as con:
            webhooks = await con.fetch("""
                SELECT
                    base
                FROM
                    webhook
                WHERE
                    show_id=$1;
            """, show_id)

        instances = []

        for wh in webhooks:
            base = await WebhookBase.from_id(app, wh["base"], with_validity=with_validity)
            if not base:
                continue

            instance = cls()

            instance._app = app

            instance.show_id = show_id
            instance.base = base
            instance.triggers = await instance.get_triggers()

            instances.append(instance)

        return instances

    @classmethod
    async def from_composite(cls, app: Any, show_id: int, base_id: int) -> Optional[Webhook]:
        """
        Returns a webhook from its composite key.

        Parameters
        ----------
        app: Any
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
                    base
                FROM
                    webhook
                WHERE
                    show_id=$1 AND base=$2;
            """, show_id, base_id)

        base = await WebhookBase.from_id(app, webhook["base"], with_validity=False)
        if not base:
            return None

        instance = cls()

        instance._app = app

        instance.show_id = show_id
        instance.base = base
        instance.triggers = await instance.get_triggers()

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
                WHERE
                    show_id=$1 AND base=$2;
            """, self.show_id, self.base.base_id)

        self.triggers = [r["trigger"] for r in triggers]

        return self.triggers

    async def add_trigger(self, trigger: str) -> List[str]:
        """
        Adds a new trigger to a webhook.

        Parameters
        ----------
        trigger: str
            The valid trigger.

        Returns
        -------
        List[str]
            List of triggers after attempted change.
        """
        if trigger not in VALID_TRIGGERS:
            return await self.get_triggers()

        async with self._app.db_pool.acquire() as con:
            exists = await con.fetchval("""
                SELECT
                    trigger
                FROM
                    webhook_trigger
                WHERE show_id=$1 AND base=$2 AND trigger=$3;
            """, self.show_id, self.base.base_id, trigger)

            if exists:
                return await self.get_triggers()

            await con.execute("""
                INSERT INTO
                    webhook_trigger
                    (show_id, base, trigger)
                VALUES
                    ($1, $2, $3);
            """, self.show_id, self.base.base_id, trigger)

        return await self.get_triggers()

    async def remove_trigger(self, trigger: str) -> List[str]:
        """
        Removes a trigger from a webhook.

        Parameters
        ----------
        trigger: str
            The valid trigger.

        Returns
        -------
        List[str]
            List of triggers after attempted change.
        """
        if trigger not in VALID_TRIGGERS:
            return await self.get_triggers()

        async with self._app.db_pool.acquire() as con:
            exists = await con.fetchval("""
                SELECT
                    trigger
                FROM
                    webhook_trigger
                WHERE show_id=$1 AND base=$2 AND trigger=$3;
            """, self.show_id, self.base.base_id, trigger)

            if not exists:
                return await self.get_triggers()

            await con.execute("""
                DELETE FROM
                    webhook_trigger
                WHERE show_id=$1 AND base=$2 AND trigger=$3;
            """, self.show_id, self.base.base_id, trigger)

        return await self.get_triggers()

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
        return {
            "title": "Tsundoku Progress Event",
            "color": 370725,
            "description": content
        }

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

    async def generate_payload(self, episode: int, event: str) -> Optional[dict]:
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
            return None

        payload: Any = {}

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

    async def send(self, episode: int, event: str) -> None:
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
            logger.warn("Webhooks - Attempted to send webhook, but the base webhook was invalid")
            return None

        logger.debug(f"Webhooks - Generating payload for Webhook with show ID {self.show_id}")
        payload = await self.generate_payload(episode, event)

        if not payload:
            logger.warn(f"Webhooks - Failed to generate a valid payload for Webhook with show ID {self.show_id}")
            return None

        logger.debug(f"Webhooks - Payload generated for Webhook with show ID {self.show_id}")

        logger.debug(f"Webhooks - Webhook for show {self.show_id} sending payload...")

        try:
            await self._app.session.post(self.base.url, json=payload)
            logger.debug(f"Webhooks - Webhook for show {self.show_id} payload sent")
        except Exception:
            pass
