import re

import aiohttp
from quart import current_app as app


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
    embed["color"] = "#05a825"
    embed["description"] = content

    return embed


def generate_slack_block(content: str) -> dict:
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
    block = {}

    block["type"] = "section"
    block["text"] = {
        "type": "mrkdwn",
        "text": content
    }

    return block


def generate_payload(wh_id: int, show_id: int, episode: int, event: str) -> dict:
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
            SELECT title FROM shows WHERE id=$1;
        """, show_id)
        content_fmt = await con.fetchval("""
            SELECT content_fmt FROM webhook WHERE id=$1;
        """, wh_id)

    if not show_name or not content_fmt:
        return

    payload = {}

    def sub_func(match: re.Match):
        expr = match.group(1)

        keywords = {
            "name": show_name,
            "episode": episode,
            "state": event
        }

        return keywords.get(expr, expr)

    content = re.sub(r"{(\w+)}", sub_func, content_fmt)

    if service == "discord":
        # Discord expects an array
        payload["embeds"] = [generate_discord_embed(content)]
    elif service == "slack":
        # Slack also expects an array
        payload["text"] = "Tsundoku Progress Event"
        payload["blocks"] = [generate_slack_block(content)]
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
    payload = generate_payload(wh_id, show_id, episode, event)

    if not payload:
        return

    async with app.db_pool.acquire() as con:
        url = await con.fetchval("""
            SELECT wh_url FROM webhook WHERE id=$1;
        """, wh_id)

    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, json=payload)
