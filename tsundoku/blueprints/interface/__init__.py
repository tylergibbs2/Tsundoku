import json

from quart import Blueprint, render_template
from quart import current_app as app

ux_blueprint = Blueprint('interface', __name__, template_folder="templates", static_folder="static")

@ux_blueprint.route("/", methods=["GET"])
async def index():
    return await render_template("index.html")
