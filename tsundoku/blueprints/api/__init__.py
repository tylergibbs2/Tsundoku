import json

from quart import Blueprint, Response, request
from quart import current_app as app

api_blueprint = Blueprint('api', __name__, url_prefix="/api")

@api_blueprint.route("/get_shows/", methods=["GET"])
async def get_shows():
    async with app.db_pool.acquire() as con:
        shows = await con.fetch("""
            SELECT id, search_title, desired_format, desired_folder,
            season, episode_offset FROM shows;
        """)
    return json.dumps([dict(record) for record in shows])


@api_blueprint.route("/get_show_by_id/<int:show_id>", methods=["GET"])
async def get_show_by_id(show_id: int):
    async with app.db_pool.acquire() as con:
        show = await con.fetchrow("""
            SELECT id, search_title, desired_format, desired_folder,
            season, episode_offset FROM shows WHERE id=$1;
        """, show_id)

    if not show:
        show = {}

    return json.dumps(dict(show))


@api_blueprint.route("/get_show_entries/<int:show_id>", methods=["GET"])
async def get_show_entries(show_id: int):
    async with app.db_pool.acquire() as con:
        entries = await con.fetch("""
            SELECT id, episode, current_state, torrent_hash
            FROM show_entry WHERE show_id=$1;
        """, show_id)

        return json.dumps([dict(record) for record in entries])


@api_blueprint.route("/handle_entry/", methods=["POST"])
async def handle_entry():
    required_arguments = {"show_id", "episode", "magnet"}
    await request.get_data()
    arguments = await request.form

    response = {"success": False}

    if set(arguments.keys()) != required_arguments:
        response["error"] = "too many arguments or missing required argument"
        return Response(json.dumps(response), status=400)
    
    try:
        show_id = int(arguments["show_id"])
    except ValueError:
        response["error"] = "show_id argument must be int"
        return Response(json.dumps(response), status=400)

    try:
        episode = int(arguments["episode"])
    except ValueError:
        response["error"] = "episode argument must be int"
        return Response(json.dumps(response), status=400)

    await app.downloader.begin_handling(show_id, episode, arguments["magnet"])
    response["success"] = True

    return json.dumps(response)