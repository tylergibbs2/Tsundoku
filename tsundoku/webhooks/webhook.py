from __future__ import annotations
import logging
from typing import List, Optional

from quart import current_app as app


logger = logging.getLogger("tsundoku")


class ExprDict(dict):
    def __missing__(self, value):
        return value

VALID_SERVICES = ("discord", "slack", "custom")
VALID_TRIGGERS = ("downloading", "downloaded", "renamed", "moved", "completed")


class Webhook:
    wh_id: int
    show_id: int
    service: str
    url: str
    content_fmt: str

    def to_dict(self) -> dict:
        """
        Return the Webhook object as a dict.

        Returns
        -------
        dict
            The dict.
        """
        return {
            "wh_id": self.wh_id,
            "show_id": self.show_id,
            "service": self.service,
            "url": self.url,
            "content_fmt": self.content_fmt
        }

    @classmethod
    async def new(cls, show_id: int, service: str, url: str, content_fmt: Optional[str]=None) -> Optional[Webhook]:
        """
        Adds a new Webhook to the database and
        returns an instance.

        Parameters
        ----------
        show_id: int
            The show's ID.
        service: str
            The webhook service.
        url: str
            The URL the webhook posts to.
        content_fmt: Optional[str]
            The content format string.

        Returns
        -------
        Optional[Webhook]
            The new Webhook.
        """
        if service not in VALID_SERVICES:
            return

        async with app.db_pool.acquire() as con:
            new_wh = await con.fetchrow("""
                INSERT INTO
                    webhook
                    (show_id, wh_service, wh_url, content_fmt)
                VALUES
                    ($1, $2, $3, $4)
                RETURNING id, content_fmt;
            """, show_id, service, url, content_fmt)

        if not new_wh:
            return

        instance = cls()

        instance.wh_id = new_wh["id"]
        instance.show_id = show_id
        instance.service = service
        instance.url = url
        instance.content_fmt = new_wh["content_fmt"]

        return instance

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

        async with app.db_pool.acquire() as con:
            updated = await con.fetchval("""
                UPDATE
                    webhook
                SET
                    show_id=$1,
                    wh_service=$2,
                    wh_url=$3,
                    content_fmt=$4
                WHERE
                    id=$5
                RETURNING id;
            """, self.show_id, self.service, self.url, self.content_fmt, self.wh_id)

        if not updated:
            return False

        return True

    async def delete(self) -> bool:
        """
        Deletes a Webhook from the database.

        Returns
        -------
        bool:
            Whether the webhook was deleted or not.
        """
        async with app.db_pool.acquire() as con:
            deleted = await con.fetchval("""
                DELETE FROM
                    webhook
                WHERE wh_id=$1
                RETURNING id;
            """, self.wh_id)

        return bool(deleted)

    @classmethod
    async def from_wh_id(cls, wh_id: int) -> Optional[Webhook]:
        """
        Returns a Webhook object from a webhook ID.

        Parameters
        ----------
        wh_id: int
            The Webhook's ID.

        Returns
        -------
        Optional[Webhook]
            The requested webhook.
        """
        async with app.db_pool.acquire() as con:
            wh = await con.fetchrow("""
                SELECT
                    show_id, wh_service, wh_url, content_fmt
                FROM
                    webhook
                WHERE id=$1;
            """, wh_id)

        if not wh:
            return

        instance = cls()

        instance.wh_id = wh_id
        instance.show_id = wh["show_id"]
        instance.service = wh["wh_service"]
        instance.url = wh["wh_url"]
        instance.content_fmt = wh["content_fmt"]

        return instance

    @classmethod
    async def from_show_id(cls, show_id: int) -> List[Webhook]:
        """
        Returns all webhooks for a specified show ID.

        Parameters
        ----------
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
                    id, wh_service, wh_url, content_fmt
                FROM
                    webhook
                WHERE show_id=$1;
            """, show_id)

        instances = []

        for wh in webhooks:
            instance = cls()

            instance.wh_id = wh["id"]
            instance.show_id = show_id
            instance.service = wh["wh_service"]
            instance.url = wh["wh_url"]
            instance.content_fmt = wh["content_fmt"]

            instances.append(instance)

        return instances

    async def get_triggers(self) -> List[str]:
        """
        Retrieves all triggers for a webhook.

        Returns
        -------
        List[str]
            All valid triggers.
        """
        async with app.db_pool.acquire() as con:
            triggers = await con.fetch("""
                SELECT
                    trigger
                FROM
                    wh_trigger
                WHERE wh_id=$1;
            """, self.wh_id)

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

        async with app.db_pool.acquire() as con:
            exists = await con.fetchval("""
                SELECT
                    trigger
                FROM
                    wh_trigger
                WHERE wh_id=$1 AND trigger=$2;
            """, self.wh_id, trigger)

            if exists:
                return True

            await con.execute("""
                INSERT INTO
                    wh_trigger
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

        async with app.db_pool.acquire() as con:
            exists = await con.fetchval("""
                SELECT
                    trigger
                FROM
                    wh_trigger
                WHERE wh_id=$1 AND trigger=$2;
            """, self.wh_id, trigger)

            if not exists:
                return False

            await con.execute("""
                DELETE FROM
                    wh_trigger
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
        async with app.db_pool.acquire() as con:
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

        content = self.content_fmt.format_map(expr)

        if self.service == "discord":
            # Discord expects an array
            payload["embeds"] = [self.generate_discord_embed(content)]
        elif self.service == "slack":
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
        logger.debug(f"Webhooks - Generating payload for Webhook with ID {self.wh_id}")
        payload = await self.generate_payload(episode, event)

        if not payload:
            logger.warn(f"Webhooks - Failed to generate a valid payload for Webhook with ID {self.wh_id}")
            return

        logger.debug(f"Webhooks - Payload generated for Webhook with ID {self.wh_id}")

        logger.debug(f"Webhooks - Webhook {self.wh_id} sending payload...")
        await app.session.post(self.url, json=payload)
