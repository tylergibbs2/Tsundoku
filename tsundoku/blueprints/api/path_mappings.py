import asyncio
from pathlib import Path
import sqlite3

from fastapi import APIRouter, status

from tsundoku.auth import StateDep
from tsundoku.manager import PathMapping
from tsundoku.utils import directory_is_writable

from .response import APIError, Success
from .schemas import PathMappingCreate, PathMappingUpdate

router = APIRouter()


def _describe_local_prefix_problem(local_prefix: str) -> str | None:
    """Why ``local_prefix`` is unusable, or ``None`` if it is fine.

    Checked when a mapping is saved rather than in the model, because loading
    must never fail: a mount that disappears should not stop existing mappings
    from being read back. Writability matters as much as existence -- renames
    happen in place in the download directory and the trailing symlink is
    written there too, so a read-only mount would fail deep in the pipeline.
    """
    path = Path(local_prefix)

    if not path.is_dir():
        return f"'{local_prefix}' does not exist inside Tsundoku, or is not a directory."
    if not directory_is_writable(path):
        return f"'{local_prefix}' is not writable by Tsundoku."

    return None


async def _validate_local_prefix(local_prefix: str) -> None:
    problem = await asyncio.to_thread(_describe_local_prefix_problem, local_prefix)
    if problem is not None:
        raise APIError(status.HTTP_422_UNPROCESSABLE_CONTENT, problem)


@router.get("/path_mappings")
async def get_path_mappings(state: StateDep) -> Success[list[PathMapping]]:
    return Success(result=await PathMapping.all(state))


@router.get("/path_mappings/{mapping_id}")
async def get_path_mapping(state: StateDep, mapping_id: int) -> Success[PathMapping]:
    try:
        mapping = await PathMapping.from_id(state, mapping_id)
    except ValueError as e:
        raise APIError(status.HTTP_404_NOT_FOUND, "Path mapping with specified ID does not exist.") from e

    return Success(result=mapping)


@router.post("/path_mappings", status_code=status.HTTP_201_CREATED)
async def create_path_mapping(state: StateDep, body: PathMappingCreate) -> Success[PathMapping]:
    await _validate_local_prefix(body.local_prefix)

    try:
        mapping = await PathMapping.new(state, body.remote_prefix, body.local_prefix)
    except sqlite3.IntegrityError as e:
        raise APIError(status.HTTP_409_CONFLICT, "A mapping for that remote prefix already exists.") from e

    return Success(status=status.HTTP_201_CREATED, result=mapping)


@router.put("/path_mappings/{mapping_id}")
async def update_path_mapping(state: StateDep, mapping_id: int, body: PathMappingUpdate) -> Success[PathMapping]:
    try:
        mapping = await PathMapping.from_id(state, mapping_id)
    except ValueError as e:
        raise APIError(status.HTTP_404_NOT_FOUND, "Path mapping with specified ID does not exist.") from e

    await _validate_local_prefix(body.local_prefix)

    mapping.remote_prefix = body.remote_prefix
    mapping.local_prefix = body.local_prefix

    try:
        await mapping.save()
    except sqlite3.IntegrityError as e:
        raise APIError(status.HTTP_409_CONFLICT, "A mapping for that remote prefix already exists.") from e

    return Success(result=mapping)


@router.delete("/path_mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_path_mapping(state: StateDep, mapping_id: int) -> None:
    try:
        mapping = await PathMapping.from_id(state, mapping_id)
    except ValueError as e:
        raise APIError(status.HTTP_404_NOT_FOUND, "Path mapping with specified ID does not exist.") from e

    await mapping.delete()
