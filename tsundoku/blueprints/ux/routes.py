import os
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from quart import Blueprint, abort
from quart import current_app as app
from quart import flash, redirect, render_template, request, url_for
from quart_auth import current_user, login_required, login_user, logout_user

from tsundoku import __version__ as version
from tsundoku.fluent import get_injector
from tsundoku.git import check_for_updates, update
from tsundoku.kitsu import KitsuManager
from tsundoku.user import User
from tsundoku.webhooks import Webhook, WebhookBase

ux_blueprint = Blueprint(
    'ux',
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/ux/static"
)
hasher = PasswordHasher()


@ux_blueprint.context_processor
async def update_context() -> dict:
    async with app.db_pool.acquire() as con:
        shows = await con.fetchval("""
            SELECT
                COUNT(*)
            FROM
                shows;
        """)
        entries = await con.fetchval("""
            SELECT
                COUNT(*)
            FROM
                show_entry;
        """)

    stats = {
        "shows": shows,
        "entries": entries,
        "seen": len(app.seen_titles),
        "version": version
    }

    return {
        "stats": stats,
        "updates": app.update_info,
        "docker": os.environ.get("IS_DOCKER", False)
    }


@ux_blueprint.route("/", methods=["GET"])
@login_required
async def index() -> str:
    ctx = {}

    resources = [
        "base",
        "errors",
        "index"
    ]

    fluent = get_injector(resources)
    ctx["_"] = fluent.format_value

    status_html_map = {
        "current": f"<span class='img-overlay-span tag is-success'>{fluent._('status-airing')}</span>",
        "finished": f"<span class='img-overlay-span tag is-danger'>{fluent._('status-finished')}</span>",
        "tba": f"<span class='img-overlay-span tag is-warning'>{fluent._('status-tba')}</span>",
        "unreleased": f"<span class='img-overlay-span tag is-info'>{fluent._('status-unreleased')}</span>",
        "upcoming": f"<span class='img-overlay-span tag is-primary'>{fluent._('status-upcoming')}</span>"
    }

    async with app.db_pool.acquire() as con:
        shows = await con.fetch("""
            SELECT
                id,
                title,
                desired_format,
                desired_folder,
                season,
                episode_offset
            FROM
                shows
            ORDER BY title;
        """)
        shows = [dict(s) for s in shows]
        for s in shows:
            entries = await con.fetch("""
                SELECT
                    id,
                    show_id,
                    episode,
                    current_state
                FROM
                    show_entry
                WHERE show_id=$1
                ORDER BY episode ASC;
            """, s["id"])
            s["entries"] = [dict(e) for e in entries]
            for e in s["entries"]:
                e["current_state"] = fluent.format_value(f"entry-status-{e['current_state']}")

            s["webhooks"] = []
            webhooks = await Webhook.from_show_id(app, s["id"])
            for webhook in webhooks:
                triggers = await webhook.get_triggers()
                wh = webhook.to_dict()
                wh["triggers"] = triggers
                s["webhooks"].append(wh)

            manager = await KitsuManager.from_show_id(s["id"])
            if manager:
                status = await manager.get_status()
                if status:
                    s["status"] = status_html_map[status]
                s["kitsu_id"] = manager.kitsu_id
                s["image"] = await manager.get_poster_image()
                s["link"] = manager.link

    ctx["shows"] = shows
    ctx["bases"] = [b.to_dict() for b in await WebhookBase.all(app)]
    ctx["seen_titles"] = list(app.seen_titles)

    if not len(app.rss_parsers):
        await flash(fluent._("no-rss-parsers"))
    elif not len(app.seen_titles):
        await flash(fluent._("no-shows-found"))

    return await render_template("index.html", **ctx)


@ux_blueprint.route("/nyaa", methods=["GET"])
@login_required
async def nyaa_search() -> str:
    ctx = {}

    resources = [
        "base"
    ]

    fluent = get_injector(resources)
    ctx["_"] = fluent.format_value

    async with app.db_pool.acquire() as con:
        shows = await con.fetch("""
            SELECT
                id,
                title
            FROM
                shows
            ORDER BY title;
        """)
        ctx["shows"] = [dict(s) for s in shows]

    ctx["seen_titles"] = list(app.seen_titles)

    return await render_template("nyaa_search.html", **ctx)


@ux_blueprint.route("/webhooks", methods=["GET"])
@login_required
async def webhooks() -> str:
    ctx = {}

    resources = [
        "base",
        "webhooks"
    ]

    fluent = get_injector(resources)
    ctx["_"] = fluent.format_value

    all_bases = await WebhookBase.all(app)
    ctx["bases"] = [b.to_dict() for b in all_bases]

    return await render_template("webhooks.html", **ctx)


@ux_blueprint.route("/update", methods=["GET", "POST"])
@login_required
async def update_() -> Any:
    if request.method == "GET":
        check_for_updates()
    else:
        await update()

    return redirect(url_for("ux.index"))


@ux_blueprint.route("/login", methods=["GET", "POST"])
async def login() -> Any:
    if await current_user.is_authenticated:
        return redirect(url_for("ux.index"))

    if request.method == "GET":
        fluent = get_injector(["login"])
        return await render_template("login.html", **{"_": fluent.format_value})
    else:
        resources = [
            "login"
        ]
        fluent = get_injector(resources)

        form = await request.form

        username = form.get("username")
        password = form.get("password")
        if username is None or password is None:
            return abort(400, fluent._("form-missing-data"))

        async with app.db_pool.acquire() as con:
            user_data = await con.fetchrow("""
                SELECT
                    id,
                    password_hash
                FROM
                    users
                WHERE LOWER(username) = $1;
            """, username.lower())

        if not user_data:
            return abort(401, fluent._("invalid-credentials"))

        try:
            hasher.verify(user_data["password_hash"], password)
        except VerifyMismatchError:
            return abort(401, fluent._("invalid-credentials"))

        if hasher.check_needs_rehash(user_data["password_hash"]):
            async with app.db_pool.acquire() as con:
                await con.execute("""
                    UPDATE
                        users
                    SET
                        password_hash=$1
                    WHERE username=$2;
                """, hasher.hash(password), username)

        remember = form.get("remember", False)

        login_user(User(user_data["id"]), remember=remember)

        return redirect(url_for("ux.index"))


@ux_blueprint.route("/logout", methods=["GET"])
@login_required
async def logout() -> Any:
    logout_user()
    return redirect(url_for("ux.index"))
