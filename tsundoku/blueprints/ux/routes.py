import os
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from quart import Blueprint
from quart import current_app as app
from quart import flash, redirect, render_template, request, url_for
from quart_auth import current_user, login_required, login_user, logout_user

from tsundoku import __version__ as version
from tsundoku.fluent import get_injector
from tsundoku.git import check_for_updates, update
from tsundoku.manager import ShowCollection
from tsundoku.user import User
from tsundoku.webhooks import WebhookBase

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

    shows = await ShowCollection.all()
    await shows.gather_statuses()

    ctx["shows"] = shows.to_list()
    ctx["bases"] = [b.to_dict() for b in await WebhookBase.all(app, with_validity=False)]
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
            await flash(fluent._("form-missing-data"))
            return redirect(url_for("ux.login"))

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
            await flash(fluent._("invalid-credentials"))
            return redirect(url_for("ux.login"))

        try:
            hasher.verify(user_data["password_hash"], password)
        except VerifyMismatchError:
            await flash(fluent._("invalid-credentials"))
            return redirect(url_for("ux.login"))

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
