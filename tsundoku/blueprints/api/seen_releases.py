from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

    app: TsundokuApp
else:
    from quart import current_app as app

from quart import request, views

from tsundoku.manager import SeenRelease

from .response import APIResponse

logger = logging.getLogger("tsundoku")


class SeenReleasesAPI(views.MethodView):
    async def get(self, action: str) -> APIResponse:
        if action == "filter":
            title = request.args.get("title")
            release_group = request.args.get("release_group")
            resolution = request.args.get("resolution")
            episode = request.args.get("episode", default=None, type=int)
            return APIResponse(
                result=[
                    release.to_dict()
                    for release in await SeenRelease.filter(
                        app,
                        title=title,
                        release_group=release_group,
                        resolution=resolution,
                        episode=episode,
                    )
                ]
            )
        elif action == "distinct":
            field = request.args.get("field")
            if field is None:
                return APIResponse(status=400, error="Missing field argument.")

            title = request.args.get("title")
            release_group = request.args.get("release_group")
            resolution = request.args.get("resolution")
            return APIResponse(
                result=await SeenRelease.distinct(
                    app,
                    field,
                    title=title,
                    release_group=release_group,
                    resolution=resolution,
                )
            )
        else:
            return APIResponse(
                status=404, error="Unknown action. Expected 'distinct' or 'filter'."
            )
