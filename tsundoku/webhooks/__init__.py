import logging
import re
from typing import List

import aiohttp
from quart import current_app as app


logger = logging.getLogger("tsundoku")


class ExprDict(dict):
    def __missing__(self, value):
        return value


def generate_discord_embed(content: str) -> dict:
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


def generate_slack_blocks(content: str) -> List[dict]:
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


async def generate_payload(wh_id: int, show_id: int, episode: int, event: str) -> dict:
    """
    Generates the complete payload for
    a webhook send.

    Parameters
    ----------
    wh_id: int
        The ID of the webhook.
    show_id: int
        The ID of the show that's being referred to.
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
        """, show_id)
        webhook = await con.fetchrow("""
            SELECT
                wh_service as service,
                content_fmt
            FROM
                webhook
            WHERE id=$1;
        """, wh_id)
    service = webhook.get("service")
    content_fmt = webhook.get("content_fmt")

    if not show_name or not content_fmt or not service:
        return

    payload = {}

    expr = ExprDict(
        name=show_name,
        episode=episode,
        state=event
    )

    content = content_fmt.format_map(expr)

    if service == "discord":
        # Discord expects an array
        payload["embeds"] = [generate_discord_embed(content)]
    elif service == "slack":
        payload["blocks"] = generate_slack_blocks(content)
    else:
        payload["content"] = content
        payload["text"] = content

    return payload


async def send(wh_id: int, show_id: int, episode: int, event: str):
    """
    Posts an event with data to a webhook.

    Parameters
    ----------
    wh_id: int
        The ID of the webhook.
    show_id: int
        The ID of the show that the post is about.
    event: str
        The event that occurred, can be any `show_state`.
    """
    logger.debug(f"Webhooks - Generating payload for Webhook with ID {wh_id}")
    payload = await generate_payload(wh_id, show_id, episode, event)

    if not payload:
        logger.warn(f"Webhooks - Failed to generate a valid payload for Webhook with ID {wh_id}")
        return

    logger.debug(f"Webhooks - Payload generated for Webhook with ID {wh_id}")

    async with app.db_pool.acquire() as con:
        url = await con.fetchval("""
            SELECT
                wh_url
            FROM
                webhook
            WHERE id=$1;
        """, wh_id)

    logger.debug(f"Webhooks - Webhook {wh_id} sending payload...")
    await app.session.post(url, json=payload)
