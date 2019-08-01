import json

from quart import Blueprint, render_template
from quart import current_app as app

ux_blueprint = Blueprint(
    'ux',
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/ux/static"
)

@ux_blueprint.route("/", methods=["GET"])
async def index():
    kwargs = {}
    async with app.db_pool.acquire() as con:
        shows = await con.fetch("""
            SELECT id, title, desired_format, desired_folder,
            season, episode_offset FROM shows ORDER BY title;
        """)
        shows = [dict(s) for s in shows]
        for s in shows:
            entries = await con.fetch("""
                SELECT id, episode, current_state FROM
                show_entry WHERE show_id=$1 ORDER BY episode ASC;
            """, s["id"])
            s["entries"] = [dict(e) for e in entries]

    kwargs["shows"] = shows

    return await render_template("index.html", **kwargs)
