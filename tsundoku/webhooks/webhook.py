from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from tsundoku.app import TsundokuApp

logger = logging.getLogger("tsundoku")


class ExprDict(dict):
    def __missing__(self, value: str) -> str:
        return value


VALID_SERVICES = ("discord", "slack", "custom")
VALID_TRIGGERS = (
    "downloading",
    "downloaded",
    "renamed",
    "moved",
    "completed",
    "failed",
)


class WebhookBase:
    _app: TsundokuApp

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
            "valid": self.valid,
        }

    @classmethod
    async def new(
        cls,
        app: Any,
        name: str,
        service: str,
        url: str,
        content_fmt: Optional[str] = None,
    ) -> Optional[WebhookBase]:
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
                    webhook_base (
                        name,
                        base_service,
                        base_url,
                        content_fmt
                    )
                VALUES
                    (?, ?, ?, ?);
            """
            args += (content_fmt,)
        else:
            query = """
                INSERT INTO
                    webhook_base
                    (name, base_service, base_url)
                VALUES
                    (?, ?, ?);
            """

        async with app.acquire_db() as con:
            await con.execute(query, *args)
            await con.execute(
                """
                SELECT
                    id,
                    content_fmt
                FROM
                    webhook_base
                WHERE
                    id = ?;
            """,
                con.lastrowid,
            )
            new_base = await con.fetchone()

        if not new_base:
            return None

        async with app.acquire_db() as con:
            await con.execute(
                """
                INSERT OR IGNORE INTO
                    webhook
                    (show_id, base)
                SELECT id, (?) FROM shows;
            """,
                new_base["id"],
            )

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
    async def from_id(
        cls, app: TsundokuApp, base_id: int, with_validity: bool = True
    ) -> Optional[WebhookBase]:
        """
        Returns a WebhookBase object from a webhook base ID.

        Parameters
        ----------
        app: TsundokuApp
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
        async with app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    id,
                    name,
                    base_service,
                    base_url,
                    content_fmt
                FROM
                    webhook_base
                WHERE
                    id=?;
            """,
                base_id,
            )
            base = await con.fetchone()

        if not base:
            return None

        async with app.acquire_db() as con:
            await con.execute(
                """
                INSERT OR IGNORE INTO
                    webhook
                    (show_id, base)
                SELECT id, (?) FROM shows;
            """,
                base_id,
            )

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
    async def from_data(
        cls, app: TsundokuApp, data: Dict[str, str], with_validity: bool = True
    ) -> WebhookBase:
        """
        Returns a WebhookBase object from passed data.

        Parameters
        ----------
        app: TsundokuApp
            The app.
        data: Dict[str, str]
            The data.
        with_validity: bool
            Whether or not to grab the WebhookBase valid state.

        Returns
        -------
        WebhookBase
            The requested webhook base.
        """
        instance = cls()

        instance._app = app

        instance.base_id = int(data["id"])
        instance.name = data["name"]
        instance.service = data["base_service"]
        instance.url = data["base_url"]
        instance.content_fmt = data["content_fmt"]

        if with_validity:
            instance.valid = await instance.is_valid()
        else:
            instance.valid = None

        return instance

    @classmethod
    async def all(
        cls, app: TsundokuApp, with_validity: bool = True
    ) -> List[WebhookBase]:
        """
        Returns all WebhookBase rows from
        the database.

        Parameters
        ----------
        app: TsundokuApp
            The app.
        with_validity: bool
            Whether to fetch if base is valid.

        Returns
        -------
        List[WebhookBase]
            All rows.
        """
        async with app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    id
                FROM
                    webhook_base
                ORDER BY
                    id ASC;
            """
            )
            ids = await con.fetchall()

        instances: List[WebhookBase] = []
        for id_ in ids:
            wh_base = await WebhookBase.from_id(
                app, id_["id"], with_validity=with_validity
            )
            if wh_base:
                instances.append(wh_base)

        return instances

    async def save(self) -> None:
        """
        Saves the attributes of the object
        to the database.
        """
        if self.service not in VALID_SERVICES or not self.content_fmt:
            return

        async with self._app.acquire_db() as con:
            await con.execute(
                """
                UPDATE
                    webhook_base
                SET
                    name=?,
                    base_service=?,
                    base_url=?,
                    content_fmt=?
                WHERE
                    id=?;
            """,
                self.name,
                self.service,
                self.url,
                self.content_fmt,
                self.base_id,
            )

    async def delete(self) -> None:
        """
        Deletes a WebhookBase from the database.
        """
        async with self._app.acquire_db() as con:
            await con.execute(
                """
                DELETE FROM
                    webhook_base
                WHERE
                    id=?;
            """,
                self.base_id,
            )

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
    _app: TsundokuApp

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
            "triggers": self.triggers,
        }

    @classmethod
    async def from_show_id(
        cls, app: TsundokuApp, show_id: int, with_validity: bool = False
    ) -> List[Webhook]:
        """
        Returns all webhooks for a specified show ID.

        Parameters
        ----------
        app: TsundokuApp
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
        async with app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    wh.base,
                    wh_b.id,
                    wh_b.name,
                    wh_b.base_service,
                    wh_b.base_url,
                    wh_b.content_fmt
                FROM
                    webhook as wh
                LEFT JOIN
                    webhook_base as wh_b
                ON
                    wh.base=wh_b.id
                WHERE
                    show_id=?;
            """,
                show_id,
            )
            webhooks = await con.fetchall()

            await con.execute(
                """
                SELECT
                    base,
                    trigger
                FROM
                    webhook_trigger
                WHERE
                    show_id=?;
            """,
                show_id,
            )
            triggers = await con.fetchall()

        instances = []

        for wh in webhooks:
            base = await WebhookBase.from_data(
                app, dict(wh), with_validity=with_validity
            )
            if not base:
                continue

            instance = cls()

            instance._app = app

            instance.show_id = show_id
            instance.base = base
            instance.triggers = [
                t["trigger"] for t in triggers if t["base"] == base.base_id
            ]

            instances.append(instance)

        return instances

    @classmethod
    async def from_composite(
        cls, app: TsundokuApp, show_id: int, base_id: int
    ) -> Optional[Webhook]:
        """
        Returns a webhook from its composite key.

        Parameters
        ----------
        app: TsundokuApp
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
        async with app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    base
                FROM
                    webhook
                WHERE
                    show_id=? AND base=?;
            """,
                show_id,
                base_id,
            )
            webhook = await con.fetchone()

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
        async with self._app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    trigger
                FROM
                    webhook_trigger
                WHERE
                    show_id=? AND base=?;
            """,
                self.show_id,
                self.base.base_id,
            )
            triggers = await con.fetchall()

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

        async with self._app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    trigger
                FROM
                    webhook_trigger
                WHERE show_id=? AND base=? AND trigger=?;
            """,
                self.show_id,
                self.base.base_id,
                trigger,
            )
            exists = await con.fetchval()

            if exists:
                return await self.get_triggers()

            await con.execute(
                """
                INSERT INTO
                    webhook_trigger
                    (show_id, base, trigger)
                VALUES
                    (?, ?, ?);
            """,
                self.show_id,
                self.base.base_id,
                trigger,
            )

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

        async with self._app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    trigger
                FROM
                    webhook_trigger
                WHERE show_id=? AND base=? AND trigger=?;
            """,
                self.show_id,
                self.base.base_id,
                trigger,
            )
            exists = await con.fetchval()

            if not exists:
                return await self.get_triggers()

            await con.execute(
                """
                DELETE FROM
                    webhook_trigger
                WHERE show_id=? AND base=? AND trigger=?;
            """,
                self.show_id,
                self.base.base_id,
                trigger,
            )

        return await self.get_triggers()

    def generate_discord_embed(self, status: str, content: str) -> dict:
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
        color: int = 0
        if status == "completed":
            color = 370725
        elif status == "failed":
            color = 16711680
        else:
            color = 16776960

        return {
            "title": "Tsundoku Progress Event",
            "color": color,
            "description": content,
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
            "text": {"type": "plain_text", "text": "Tsundoku Progress Event"},
        }

        content_block = {
            "type": "section",
            "text": {"type": "plain_text", "text": content},
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
        async with self._app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    title
                FROM
                    shows
                WHERE id=?;
            """,
                self.show_id,
            )
            show_name = await con.fetchval()

        if not show_name:
            return None

        payload: Any = {}

        expr = ExprDict(name=show_name, episode=episode, state=event)

        content = self.base.content_fmt.format_map(expr)

        if self.base.service == "discord":
            # Discord expects an array
            payload["embeds"] = [self.generate_discord_embed(event, content)]
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
            logger.warn(
                "Webhooks - Attempted to send webhook, but the base webhook was invalid"
            )
            return None

        logger.debug(f"Webhooks - Generating payload for webhook for <s{self.show_id}>")
        payload = await self.generate_payload(episode, event)

        if not payload:
            logger.warn(
                f"Webhooks - Failed to generate a valid payload for webhook for <s{self.show_id}>"
            )
            return None

        logger.debug(f"Webhooks - Payload generated for webhook for <s{self.show_id}>")

        logger.debug(
            f"Webhooks - Webhook for show <s{self.show_id}> sending payload..."
        )

        try:
            await self._app.session.post(self.base.url, json=payload)
            logger.debug(f"Webhooks - Webhook for show <s{self.show_id}> payload sent")
        except Exception:
            pass
