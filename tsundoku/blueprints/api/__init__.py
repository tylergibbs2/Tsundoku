import json
import typing

from quart import Blueprint
from quart import current_app as app

from .shows import ShowsAPI
from .entries import EntriesAPI


api_blueprint = Blueprint('api', __name__, url_prefix="/api")


@api_blueprint.route("/shows/seen", methods=["GET"])
async def get_seen_shows():
    """
    Returns a list of shows that the program
    has seen while scraping RSS feeds.

    Returns
    -------
    typing.List[str]
    """
    return json.dumps(list(app.seen_titles))


def setup_views():
    # Setup ShowsAPI URL rules.
    shows_view = ShowsAPI.as_view("shows_api")

    api_blueprint.add_url_rule(
        "/shows/",
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
        "/shows/<int:show_id>/entries/",
        defaults={
            "entry_id": None
        },
        view_func=entries_view,
        methods=["GET"]
    )
    api_blueprint.add_url_rule(
        "/shows/<int:show_id>/entries/<int:entry_id>",
        view_func=entries_view,
        methods=["GET", "POST", "DELETE"]
    )

setup_views()
