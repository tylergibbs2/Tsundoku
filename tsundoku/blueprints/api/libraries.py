from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp
    from tsundoku.user import User

    app: TsundokuApp
    current_user: User
else:
    from quart import current_app as app

from quart import request, views

from tsundoku.manager import Library

from .response import APIResponse


class LibrariesAPI(views.MethodView):
    async def get(self, library_id: int | None = None) -> APIResponse:
        if not library_id:
            return APIResponse(result=[library.to_dict() for library in await Library.all(app)])

        library = await Library.from_id(app, library_id)
        if library:
            return APIResponse(result=[library.to_dict()])

        return APIResponse(status=404, error="Library with specified ID does not exist.")

    async def post(self) -> APIResponse:
        arguments = await request.get_json()

        folder = Path(arguments.get("folder"))
        library = await Library.new(app, folder, is_default=False)

        if library:
            return APIResponse(result=library.to_dict())
        return APIResponse(status=500, error="The server failed to create the new Library.")

    async def put(self, library_id: int) -> APIResponse:
        arguments = await request.get_json()

        folder = Path(arguments.get("folder"))
        is_default = arguments.get("is_default")

        library = await Library.from_id(app, library_id)

        if not library:
            return APIResponse(status=404, error="Library with specified ID does not exist.")

        library.folder = folder
        await library.save()
        if is_default:
            await library.set_default()

        return APIResponse(result=library.to_dict())

    async def delete(self, library_id: int) -> APIResponse:
        library = await Library.from_id(app, library_id)
        if not library:
            return APIResponse(status=404, error="Library with specified ID does not exist.")

        await library.delete()
        return APIResponse(result=library.to_dict())
