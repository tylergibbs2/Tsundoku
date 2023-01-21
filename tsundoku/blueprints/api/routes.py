import logging
import sqlite3
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from quart import Blueprint

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

    app: TsundokuApp
else:
    from quart import current_app as app

from quart import request
from quart_auth import current_user

from tsundoku.config import (
    ConfigCheckFailure,
    ConfigInvalidKey,
    EncodeConfig,
    FeedsConfig,
    GeneralConfig,
    TorrentConfig,
)
from tsundoku.manager import Show

from .show_entries import ShowEntriesAPI
from .entries import EntriesAPI
from .nyaa import NyaaAPI
from .response import APIResponse
from .shows import ShowsAPI
from .webhookbase import WebhookBaseAPI
from .webhooks import WebhooksAPI
from .seen_releases import SeenReleasesAPI

api_blueprint = Blueprint("api", __name__, url_prefix="/api/v1")
logger = logging.getLogger("tsundoku")


@api_blueprint.errorhandler(500)
async def err_500(_) -> APIResponse:
    return APIResponse(status=500, error="Server encountered an unexpected error.")


@api_blueprint.before_request
async def ensure_auth() -> Optional[APIResponse]:
    authed = False
    if request.headers.get("Authorization"):
        token = request.headers["Authorization"]
        if not token.startswith("Bearer "):
            return APIResponse(status=401, error="Invalid authorization header.")
        token = token[7:]

        async with app.acquire_db() as con:
            try:
                user = await con.fetchval(
                    """
                    SELECT
                        id
                    FROM
                        users
                    WHERE
                        api_key=?;
                """,
                    token,
                )

                if user:
                    authed = True
            except Exception:
                pass
    if not authed and await current_user.is_authenticated:
        authed = True

    if not authed:
        return APIResponse(
            status=401, result="You are not authorized to access this resource."
        )

    return None


@api_blueprint.route("/config/token", methods=["GET", "POST"])
async def config_token() -> APIResponse:
    api_key = request.headers.get("Authorization") or await current_user.api_key  # type: ignore
    if request.method == "POST":
        async with app.acquire_db() as con:
            new_key = str(uuid4())
            await con.execute(
                """
                UPDATE
                    users
                SET
                    api_key = ?
                WHERE
                    api_key = ?;
            """,
                new_key,
                api_key,
            )
    else:
        new_key = api_key

    return APIResponse(status=200, result=str(new_key))


@api_blueprint.route("/config/<string:cfg_type>", methods=["GET", "PATCH"])
async def config_route(cfg_type: str) -> APIResponse:
    if cfg_type == "general":
        cfg_class = GeneralConfig
    elif cfg_type == "feeds":
        cfg_class = FeedsConfig
    elif cfg_type == "encode":
        cfg_class = EncodeConfig
    elif cfg_type == "torrent":
        cfg_class = TorrentConfig
    else:
        return APIResponse(status=400, error="Invalid configuration type.")

    cfg = await cfg_class.retrieve(app)

    if request.method == "PATCH":
        arguments = await request.get_json()

        try:
            cfg.update(arguments)
        except ConfigInvalidKey:
            return APIResponse(
                status=400, error="Invalid key contained in new configuration settings."
            )

        try:
            await cfg.save()
        except (ConfigCheckFailure, sqlite3.IntegrityError):
            return APIResponse(
                status=400, error="Error inserting new configuration data."
            )

    if cfg_type == "encode":
        cfg.keys["has_ffmpeg"] = await app.encoder.has_ffmpeg()

    return APIResponse(status=200, result=cfg.keys)


@api_blueprint.route("/config/torrent/test", methods=["GET"])
async def test_torrent_client() -> APIResponse:
    res = await app.dl_client.test_client()
    app.flags.DL_CLIENT_CONNECTION_ERROR = not res
    return APIResponse(result=res)


@api_blueprint.route("/config/encode/stats", methods=["GET"])
async def get_encode_stats() -> APIResponse:
    """
    Returns a dictionary of encode statistics.

    :returns: Dict[:class:`str`, :class:`float`]
    """
    return APIResponse(result=await app.encoder.get_stats())


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

    found_items = await app.poller.poll(force=True)

    return APIResponse(result=found_items)


@api_blueprint.route("/shows/<int:show_id>/cache", methods=["DELETE"])
async def delete_show_cache(show_id: int) -> APIResponse:
    """
    Force Tsundoku to delete the metadata cache for a show.

    .. :quickref: Shows; Deletes show metadata.
    """
    logger.info(f"API - Deleting cache for Show <s{show_id}>")

    show = await Show.from_id(app, show_id)
    await show.metadata.clear_cache()
    await show.refetch()

    return APIResponse(result=show.to_dict())


def setup_views() -> None:
    # Setup ShowsAPI URL rules.
    shows_view = ShowsAPI.as_view("shows_api")

    api_blueprint.add_url_rule(
        "/shows",
        defaults={"show_id": None},
        view_func=shows_view,
        methods=["GET", "POST"],
    )
    api_blueprint.add_url_rule(
        "/shows/<int:show_id>", view_func=shows_view, methods=["GET", "PUT", "DELETE"]
    )

    # Setup EntriesAPI URL rules.
    show_entries_view = ShowEntriesAPI.as_view("show_entries_api")

    api_blueprint.add_url_rule(
        "/shows/<int:show_id>/entries",
        defaults={"entry_id": None},
        view_func=show_entries_view,
        methods=["GET", "POST"],
    )
    api_blueprint.add_url_rule(
        "/shows/<int:show_id>/entries/<int:entry_id>",
        view_func=show_entries_view,
        methods=["GET", "DELETE"],
    )

    entries_view = EntriesAPI.as_view("entries_api")

    api_blueprint.add_url_rule(
        "/entries/<int:entry_id>", view_func=entries_view, methods=["GET"]
    )

    # Setup WebhooksAPI URL rules.
    webhooks_view = WebhooksAPI.as_view("webhooks_api")

    api_blueprint.add_url_rule(
        "/shows/<int:show_id>/webhooks", view_func=webhooks_view, methods=["GET"]
    )
    api_blueprint.add_url_rule(
        "/shows/<int:show_id>/webhooks/<int:base_id>",
        view_func=webhooks_view,
        methods=["PUT"],
    )

    # Setup WebhookBaseAPI URL rules.
    webhookbase_view = WebhookBaseAPI.as_view("webhookbase_api")

    api_blueprint.add_url_rule(
        "/webhooks", view_func=webhookbase_view, methods=["GET", "POST"]
    )
    api_blueprint.add_url_rule(
        "/webhooks/<int:base_id>",
        view_func=webhookbase_view,
        methods=["GET", "PUT", "DELETE"],
    )

    seenreleases_view = SeenReleasesAPI.as_view("seenreleases_api")

    api_blueprint.add_url_rule(
        "/seen_releases/<string:action>", view_func=seenreleases_view, methods=["GET"]
    )

    # Setup NyaaAPI URL rules.
    nyaa_view = NyaaAPI.as_view("nyaa_api")

    api_blueprint.add_url_rule("/nyaa", view_func=nyaa_view, methods=["GET", "POST"])


setup_views()
