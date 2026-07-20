from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, status

from tsundoku.auth import StateDep
from tsundoku.manager import Library

from .response import APIError, Success
from .schemas import LibraryCreate, LibraryUpdate

router = APIRouter()


@router.get("/libraries")
async def get_libraries(state: StateDep) -> Success[list[Library]]:
    return Success(result=await Library.all(state))


@router.get("/libraries/{library_id}")
async def get_library(state: StateDep, library_id: int) -> Success[list[Library]]:
    try:
        library = await Library.from_id(state, library_id)
    except ValueError as e:
        raise APIError(status.HTTP_404_NOT_FOUND, "Library with specified ID does not exist.") from e

    return Success(result=[library])


@router.post("/libraries", status_code=status.HTTP_201_CREATED)
async def create_library(state: StateDep, body: LibraryCreate) -> Success[Library]:
    library = await Library.new(state, Path(body.folder), is_default=False)
    return Success(status=status.HTTP_201_CREATED, result=library)


@router.put("/libraries/{library_id}")
async def update_library(state: StateDep, library_id: int, body: LibraryUpdate) -> Success[Library]:
    try:
        library = await Library.from_id(state, library_id)
    except ValueError as e:
        raise APIError(status.HTTP_404_NOT_FOUND, "Library with specified ID does not exist.") from e

    library.folder = Path(body.folder)
    await library.save()
    if body.is_default:
        await library.set_default()

    return Success(result=library)


@router.delete("/libraries/{library_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_library(state: StateDep, library_id: int) -> None:
    try:
        library = await Library.from_id(state, library_id)
    except ValueError as e:
        raise APIError(status.HTTP_404_NOT_FOUND, "Library with specified ID does not exist.") from e

    await library.delete()
