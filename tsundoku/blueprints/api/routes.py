import logging
import sqlite3
from typing import Optional
from uuid import uuid4

from quart import Blueprint
from quart import current_app as app
from quart import request
from quart_auth import current_user

from tsundoku.feeds.encoder import VALID_SPEEDS
from tsundoku.manager import Show

from .entries import EntriesAPI
from .nyaa import NyaaAPI
from .response import APIResponse
from .shows import ShowsAPI
from .webhookbase import WebhookBaseAPI
from .webhooks import WebhooksAPI

api_blueprint = Blueprint('api', __name__, url_prefix="/api/v1")
logger = logging.getLogger("tsundoku")


@api_blueprint.before_request
async def ensure_auth() -> Optional[APIResponse]:
    authed = False
    if request.headers.get("Authorization"):
        token = request.headers["Authorization"]
        async with app.acquire_db() as con:
            try:
                await con.execute("""
                    SELECT
                        id
                    FROM
                        users
                    WHERE
                        api_key=?;
                """, token)
                user = await con.fetchval()

                if user:
                    authed = True
            except Exception:
                pass
    if not authed and await current_user.is_authenticated:
        authed = True

    if not authed:
        return APIResponse(
            status=401,
            result="You are not authorized to access this resource."
        )

    return None


@api_blueprint.route("/config/token", methods=["GET", "POST"])
async def config_token() -> APIResponse:
    api_key = request.headers.get("Authorization") or await current_user.api_key
    if request.method == "POST":
        async with app.acquire_db() as con:
            new_key = str(uuid4())
            await con.execute("""
                UPDATE
                    users
                SET
                    api_key = ?
                WHERE
                    api_key = ?;
            """, new_key, api_key)
    else:
        new_key = api_key

    return APIResponse(
        status=200,
        result=str(new_key)
    )


@api_blueprint.route("/config/encode", methods=["GET", "PATCH"])
async def config_encode() -> APIResponse:
    async with app.acquire_db() as con:
        await con.execute("""
            INSERT OR IGNORE INTO
                encode_config (
                    id
                )
            VALUES (0);
            """)

    if request.method == "PATCH":
        arguments = await request.get_json()

        CFG_KEYS = (
            "enabled",
            "quality_preset",
            "speed_preset",
            "maximum_encodes",
            "retry_on_fail",
            "timed_encoding",
            "hour_start",
            "hour_end"
        )
        if any(k not in CFG_KEYS for k in arguments.keys()):
            return APIResponse(
                status=400,
                error="Invalid configuration keys."
            )
        elif arguments.get("speed_preset") and arguments["speed_preset"] not in VALID_SPEEDS:
            return APIResponse(
                status=400,
                error="Invalid speed preset."
            )
        elif arguments.get("quality_preset") and arguments["quality_preset"] not in ("high", "low", "moderate"):
            return APIResponse(
                status=400,
                error="Invalid quality preset."
            )
        elif arguments.get("maximum_encodes") and int(arguments["maximum_encodes"]) <= 0:
            arguments["maximum_encodes"] = 1

        hour_start, hour_end = arguments.get("hour_start"), arguments.get("hour_end")
        if hour_start and hour_end and int(hour_start) >= int(hour_end):
            return APIResponse(
                status=400,
                error="Hour start cannot be after hour end."
            )

        async with app.acquire_db() as con:
            sets = ", ".join(f"{col} = ?" for col in arguments.keys())
            try:
                await con.execute(f"""
                    UPDATE
                        encode_config
                    SET
                        {sets}
                    WHERE id = 0;
                """, *arguments.values())
            except sqlite3.IntegrityError:
                return APIResponse(
                    status=400,
                    error="Error inserting new configuration data."
                )

    async with app.acquire_db() as con:
        await con.execute("""
            SELECT
                enabled,
                quality_preset,
                speed_preset,
                maximum_encodes,
                retry_on_fail,
                timed_encoding,
                hour_start,
                hour_end
            FROM
                encode_config;
        """)
        cfg = await con.fetchone()

    cfg = dict(cfg)
    cfg["has_ffmpeg"] = await app.encoder.has_ffmpeg()

    return APIResponse(
        status=200,
        result=cfg
    )


@api_blueprint.route("/shows/seen", methods=["GET"])
async def get_seen_shows() -> APIResponse:
    """
    Returns a list of distinct titles that the Tsundoku
    poller task has seen while parsing the enabled RSS feeds.

    .. :quickref: Shows; Retrieves seen shows.

    :returns: List[:class:`str`]
    """
    return APIResponse(
        result=list(app.seen_titles)
    )


@api_blueprint.route("/shows/check", methods=["GET"])
async def check_for_releases() -> APIResponse:
    """
    Forces Tsundoku to check all enabled RSS feeds for new
    title releases.

    .. note::
        The first int in the tuple is the show ID
        and the second int is the ID of the new entry.

    .. :quickref: Shows; Checks for new releases.

    :returns: List[Tuple(:class:`int`, :class:`int`)]
    """
    logger.info("API - Force New Releases Check")

    app.poller.reset_rss_cache()
    found_items = await app.poller.poll()

    return APIResponse(
        result=found_items
    )


@api_blueprint.route("/shows/<int:show_id>/cache", methods=["DELETE"])
async def delete_show_cache(show_id: int) -> APIResponse:
    """
    Force Tsundoku to delete the metadata cache for a show.

    .. :quickref: Shows; Deletes show metadata.
    """
    logger.info(f"API - Deleting cache for Show <s{show_id}>")

    show = await Show.from_id(show_id)
    await show.metadata.clear_cache()
    await show.refetch()

    return APIResponse(
        result=show.to_dict()
    )


def setup_views() -> None:
    # Setup ShowsAPI URL rules.
    shows_view = ShowsAPI.as_view("shows_api")

    api_blueprint.add_url_rule(
        "/shows",
        defaults={
            "show_id": None
        },
        view_func=shows_view,
        methods=["GET", "POST"]
    )
    api_blueprint.add_url_rule(
        "/shows/<int:show_id>",
        view_func=shows_view,
        methods=["GET", "PUT", "DELETE"]
    )

    # Setup EntriesAPI URL rules.
    entries_view = EntriesAPI.as_view("entries_api")

    api_blueprint.add_url_rule(
        "/shows/<int:show_id>/entries",
        defaults={
            "entry_id": None
        },
        view_func=entries_view,
        methods=["GET", "POST"]
    )
    api_blueprint.add_url_rule(
        "/shows/<int:show_id>/entries/<int:entry_id>",
        view_func=entries_view,
        methods=["GET", "DELETE"]
    )

    # Setup WebhooksAPI URL rules.
    webhooks_view = WebhooksAPI.as_view("webhooks_api")

    api_blueprint.add_url_rule(
        "/shows/<int:show_id>/webhooks",
        view_func=webhooks_view,
        methods=["GET"]
    )
    api_blueprint.add_url_rule(
        "/shows/<int:show_id>/webhooks/<int:base_id>",
        view_func=webhooks_view,
        methods=["PUT"]
    )

    # Setup WebhookBaseAPI URL rules.
    webhookbase_view = WebhookBaseAPI.as_view("webhookbase_api")

    api_blueprint.add_url_rule(
        "/webhooks",
        view_func=webhookbase_view,
        methods=["GET", "POST"]
    )
    api_blueprint.add_url_rule(
        "/webhooks/<int:base_id>",
        view_func=webhookbase_view,
        methods=["GET", "PUT", "DELETE"]
    )

    # Setup NyaaAPI URL rules.
    nyaa_view = NyaaAPI.as_view("nyaa_api")

    api_blueprint.add_url_rule(
        "/nyaa",
        view_func=nyaa_view,
        methods=["GET", "POST"]
    )


setup_views()
