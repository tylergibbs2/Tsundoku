import json
import typing

from quart import Blueprint, Response, request, views
from quart import current_app as app

from .shows import ShowsAPI
from .entries import EntriesAPI


api_blueprint = Blueprint('api', __name__, url_prefix="/api")
        

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
