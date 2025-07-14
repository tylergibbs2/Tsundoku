import logging
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from quart import Blueprint

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp
    from tsundoku.user import User

    app = TsundokuApp()
    current_user = User(None)
else:
    from quart import current_app as app
    from quart_auth import current_user

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from quart import request
from quart_auth import login_user
from quart_rate_limiter import RateLimitExceeded

from tsundoku.config import (
    ConfigCheckFailError,
    ConfigInvalidKeyError,
    EncodeConfig,
    FeedsConfig,
    GeneralConfig,
    TorrentConfig,
)
from tsundoku.decorators import deny_readonly
from tsundoku.user import User
from tsundoku.utils import directory_is_writable
from tsundoku.webhooks import WebhookBase

from .entries import EntriesAPI
from .libraries import LibrariesAPI
from .nyaa import NyaaAPI
from .response import APIResponse
from .seen_releases import SeenReleasesAPI
from .show_entries import ShowEntriesAPI
from .shows import ShowsAPI
from .webhookbase import WebhookBaseAPI
from .webhooks import WebhooksAPI

api_blueprint = Blueprint("api", __name__, url_prefix="/api/v1")
logger = logging.getLogger("tsundoku")


@api_blueprint.errorhandler(500)
async def err_500(_: Any) -> APIResponse:  # noqa: RUF029
    return APIResponse(status=500, error="Server encountered an unexpected error.")


@api_blueprint.errorhandler(403)
async def err_403(_: Any) -> APIResponse:  # noqa: RUF029
    return APIResponse(status=403, error="You are forbidden from modifying this resource.")


@api_blueprint.errorhandler(429)
async def err_429(e: Exception) -> APIResponse:  # noqa: RUF029
    error = "Too many requests."
    if isinstance(e, RateLimitExceeded):
        error += f" Try again in {e.retry_after} seconds."
    return APIResponse(status=429, error=error)


@api_blueprint.before_request
async def ensure_auth() -> APIResponse | None:
    if request.headers.get("Authorization"):
        token = request.headers["Authorization"]
        if not token.startswith("Bearer "):
            return APIResponse(status=401, error="Invalid authorization header.")
        token = token[7:]

        async with app.acquire_db() as con:
            try:
                user_id = await con.fetchval(
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

                if user_id:
                    login_user(User(user_id))
            except Exception:
                return APIResponse(status=401, result="You are not authorized to access this resource.")

    if not await current_user.is_authenticated:
        return APIResponse(status=401, result="You are not authorized to access this resource.")

    if await current_user.readonly and request.method in (
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    ):
        return APIResponse(status=403, error="You are forbidden from modifying this resource.")

    return None


@api_blueprint.route("/tree", methods=["POST"])
async def tree() -> APIResponse:
    data = await request.get_json()
    if "dir" not in data:
        return APIResponse(status=400, error="Missing 'dir' key in request body.")

    location = Path(data["dir"]).resolve()
    if data.get("subdir"):
        try:
            location = (location / data["subdir"]).resolve()
        except PermissionError:
            pass

    dirs = []
    for directory in location.glob("*"):
        if not directory.is_dir():
            continue

        dirs.append(directory.name)

    can_go_back = location.parent != location
    return APIResponse(
        status=200,
        result={
            "root_is_writable": directory_is_writable(location),
            "can_go_back": can_go_back,
            "current_path": str(location),
            "children": dirs,
        },
    )


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

    return APIResponse(status=200, result=new_key)


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
        except ConfigInvalidKeyError:
            return APIResponse(status=400, error="Invalid key contained in new configuration settings.")

        try:
            await cfg.save()
        except sqlite3.IntegrityError:
            return APIResponse(status=400, error="Error inserting new configuration data.")
        except ConfigCheckFailError as e:
            return APIResponse(status=400, error=e.message)

    if cfg_type == "encode":
        cfg.keys["has_ffmpeg"] = await app.encoder.has_ffmpeg()
        cfg.keys["available_encoders"] = await app.encoder.get_available_encoders()

    return APIResponse(status=200, result=cfg.keys)


@api_blueprint.route("/config/torrent/test", methods=["GET"])
@deny_readonly
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


@api_blueprint.route("/encode/queue", methods=["GET"])
async def get_encode_queue() -> APIResponse:
    """
    Returns the encoding queue.

    :returns: List[:class:`Dict`]
    """
    page = request.args.get("page", "0")
    if not page.isdigit():
        page = 0
    elif int(page) < 1:
        page = 0
    else:
        page = int(page)

    return APIResponse(result=await app.encoder.get_queue(page))


@api_blueprint.route("/shows/check", methods=["GET"])
@deny_readonly
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
    Force Tsundoku to delete the poster cache for a show.

    .. :quickref: Shows; Deletes show poster cache.
    """
    logger.info(f"API - Deleting poster cache for Show <s{show_id}>")

    async with app.acquire_db() as con:
        await con.execute(
            """
            UPDATE
                kitsu_info
            SET
                cached_poster_url = NULL
            WHERE
                show_id = ?;
        """,
            (show_id,),
        )

    return APIResponse(result=True)


@api_blueprint.route("/webhooks/<int:base_id>/valid", methods=["GET"])
async def webhook_is_valid(base_id: int) -> APIResponse:
    """
    Checks if a Webhook is valid with the service it is for.
    """
    logger.info(f"API - Checking webhook validity for webhook ID {base_id}")

    webhook = await WebhookBase.from_id(app, base_id)
    if webhook is None:
        return APIResponse(result=False)

    return APIResponse(result=await webhook.is_valid())


@api_blueprint.route("/account/change-password", methods=["POST"])
@deny_readonly
async def change_password() -> APIResponse:
    data = await request.get_json()
    if not data:
        return APIResponse(status=400, error="Missing request body.")
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    if not current_password or not new_password:
        return APIResponse(status=400, error="Missing current or new password.")
    if len(new_password) < 8:
        return APIResponse(status=400, error="New password must be at least 8 characters.")

    hasher = PasswordHasher()
    async with app.acquire_db() as con:
        user_data = await con.fetchone(
            """
            SELECT password_hash, username FROM users WHERE id = ?;
            """,
            current_user.auth_id,
        )
        if not user_data:
            return APIResponse(status=404, error="User not found.")
        try:
            hasher.verify(user_data["password_hash"], current_password)
        except VerifyMismatchError:
            return APIResponse(status=400, error="Current password is incorrect.")

        if hasher.check_needs_rehash(user_data["password_hash"]):
            new_hash = hasher.hash(current_password)
            await con.execute(
                """
                UPDATE users SET password_hash=? WHERE id=?;
                """,
                new_hash,
                current_user.auth_id,
            )

        new_hash = hasher.hash(new_password)
        await con.execute(
            """
            UPDATE users SET password_hash=? WHERE id=?;
            """,
            new_hash,
            current_user.auth_id,
        )

    return APIResponse(status=200, result=True)


def setup_views() -> None:
    # Setup ShowsAPI URL rules.
    shows_view = ShowsAPI.as_view("shows_api")

    api_blueprint.add_url_rule(
        "/shows",
        defaults={"show_id": None},
        view_func=shows_view,
        methods=["GET", "POST"],
    )
    api_blueprint.add_url_rule("/shows/<int:show_id>", view_func=shows_view, methods=["GET", "PUT", "DELETE"])

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

    api_blueprint.add_url_rule("/entries/<int:entry_id>", view_func=entries_view, methods=["GET"])

    # Setup WebhooksAPI URL rules.
    webhooks_view = WebhooksAPI.as_view("webhooks_api")

    api_blueprint.add_url_rule("/shows/<int:show_id>/webhooks", view_func=webhooks_view, methods=["GET"])
    api_blueprint.add_url_rule(
        "/shows/<int:show_id>/webhooks/<int:base_id>",
        view_func=webhooks_view,
        methods=["PUT"],
    )

    # Setup WebhookBaseAPI URL rules.
    webhookbase_view = WebhookBaseAPI.as_view("webhookbase_api")

    api_blueprint.add_url_rule("/webhooks", view_func=webhookbase_view, methods=["GET", "POST"])
    api_blueprint.add_url_rule(
        "/webhooks/<int:base_id>",
        view_func=webhookbase_view,
        methods=["GET", "PUT", "DELETE"],
    )

    seenreleases_view = SeenReleasesAPI.as_view("seenreleases_api")

    api_blueprint.add_url_rule("/seen_releases/<string:action>", view_func=seenreleases_view, methods=["GET"])

    # Setup NyaaAPI URL rules.
    nyaa_view = NyaaAPI.as_view("nyaa_api")

    api_blueprint.add_url_rule("/nyaa", view_func=nyaa_view, methods=["GET", "POST"])

    libraries_view = LibrariesAPI.as_view("libraries_api")

    api_blueprint.add_url_rule("/libraries", view_func=libraries_view, methods=["GET", "POST"])
    api_blueprint.add_url_rule(
        "/libraries/<int:library_id>",
        view_func=libraries_view,
        methods=["GET", "PUT", "DELETE"],
    )


setup_views()
