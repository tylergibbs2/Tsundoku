from __future__ import annotations

import asyncio
import logging
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, status

from tsundoku.auth import ApiUserDep, DenyReadonlyDep, StateDep, deny_readonly, require_api_user
from tsundoku.config import (
    ConfigCheckFailError,
    ConfigInvalidKeyError,
    FeedsConfig,
    GeneralConfig,
    TorrentConfig,
)
from tsundoku.feeds.poller import FoundEntry
from tsundoku.utils import directory_is_writable
from tsundoku.webhooks import WebhookBase

from .entries import router as entries_router
from .libraries import router as libraries_router
from .nyaa import router as nyaa_router
from .response import APIError, Success
from .schemas import (
    ChangePasswordRequest,
    DirectoryTree,
    FeedsConfigResponse,
    FeedsConfigUpdate,
    GeneralConfigResponse,
    GeneralConfigUpdate,
    TorrentConfigResponse,
    TorrentConfigUpdate,
    TorrentTestResult,
    TreeRequest,
)
from .seen_releases import router as seen_releases_router
from .show_entries import router as show_entries_router
from .shows import router as shows_router
from .webhookbase import router as webhookbase_router
from .webhooks import router as webhooks_router

logger = logging.getLogger("tsundoku")

api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_user)])


def _list_directory(dir_: str, subdir: str | None) -> DirectoryTree:
    location = Path(dir_).resolve()
    if subdir:
        try:
            location = (location / subdir).resolve()
        except PermissionError:
            pass

    dirs = [directory.name for directory in location.glob("*") if directory.is_dir()]

    return DirectoryTree(
        root_is_writable=directory_is_writable(location),
        can_go_back=location.parent != location,
        current_path=str(location),
        children=dirs,
    )


@api_router.post("/tree")
async def tree(body: TreeRequest) -> Success[DirectoryTree]:
    result = await asyncio.to_thread(_list_directory, body.dir, body.subdir)
    return Success(result=result)


@api_router.get("/config/token")
async def get_api_token(user: ApiUserDep) -> Success[str]:
    return Success(result=user.api_key)


@api_router.post("/config/token")
async def regenerate_api_token(state: StateDep, user: ApiUserDep) -> Success[str]:
    new_key = str(uuid4())
    async with state.acquire_db() as con:
        await con.execute(
            """
            UPDATE
                users
            SET
                api_key = ?
            WHERE
                api_key = ?;
        """,
            new_key,
            user.api_key,
        )

    return Success(result=new_key)


async def _apply_config_update(cfg: GeneralConfig | FeedsConfig | TorrentConfig, updates: dict[str, Any]) -> None:
    if not updates:
        return

    try:
        cfg.update(updates)
    except ConfigInvalidKeyError as e:
        raise APIError(status.HTTP_400_BAD_REQUEST, "Invalid key contained in new configuration settings.") from e

    try:
        await cfg.save()
    except sqlite3.IntegrityError as e:
        raise APIError(status.HTTP_400_BAD_REQUEST, "Error inserting new configuration data.") from e
    except ConfigCheckFailError as e:
        raise APIError(status.HTTP_400_BAD_REQUEST, e.message) from e


@api_router.get("/config/general")
async def get_general_config(state: StateDep) -> Success[GeneralConfigResponse]:
    cfg = await GeneralConfig.retrieve(state)
    return Success(result=GeneralConfigResponse.model_validate(cfg.keys))


@api_router.patch("/config/general")
async def update_general_config(state: StateDep, body: GeneralConfigUpdate) -> Success[GeneralConfigResponse]:
    cfg = await GeneralConfig.retrieve(state)
    await _apply_config_update(cfg, body.model_dump(exclude_unset=True))
    return Success(result=GeneralConfigResponse.model_validate(cfg.keys))


@api_router.get("/config/feeds")
async def get_feeds_config(state: StateDep) -> Success[FeedsConfigResponse]:
    cfg = await FeedsConfig.retrieve(state)
    return Success(result=FeedsConfigResponse.model_validate(cfg.keys))


@api_router.patch("/config/feeds")
async def update_feeds_config(state: StateDep, body: FeedsConfigUpdate) -> Success[FeedsConfigResponse]:
    cfg = await FeedsConfig.retrieve(state)
    await _apply_config_update(cfg, body.model_dump(exclude_unset=True))
    return Success(result=FeedsConfigResponse.model_validate(cfg.keys))


@api_router.get("/config/torrent")
async def get_torrent_config(state: StateDep) -> Success[TorrentConfigResponse]:
    cfg = await TorrentConfig.retrieve(state)
    return Success(result=TorrentConfigResponse.model_validate(cfg.keys))


@api_router.patch("/config/torrent")
async def update_torrent_config(state: StateDep, body: TorrentConfigUpdate) -> Success[TorrentConfigResponse]:
    cfg = await TorrentConfig.retrieve(state)
    await _apply_config_update(cfg, body.model_dump(exclude_unset=True))
    return Success(result=TorrentConfigResponse.model_validate(cfg.keys))


@api_router.get("/config/torrent/test", dependencies=[Depends(deny_readonly)])
async def test_torrent_client(state: StateDep) -> Success[TorrentTestResult]:
    result = await state.dl_client.test_client()
    state.flags.DL_CLIENT_CONNECTION_ERROR = not result.success
    return Success(result=TorrentTestResult(success=result.success, error=result.error))


@api_router.get("/shows/check", dependencies=[Depends(deny_readonly)])
async def check_for_releases(state: StateDep) -> Success[list[FoundEntry]]:
    """Force Tsundoku to check all enabled RSS feeds for new releases."""
    logger.info("API - Force New Releases Check")
    found_items = await state.poller.poll(force=True)
    return Success(result=found_items)


@api_router.delete("/shows/{show_id}/cache", status_code=status.HTTP_204_NO_CONTENT)
async def delete_show_cache(state: StateDep, show_id: int) -> None:
    """Force Tsundoku to delete the poster cache for a show."""
    logger.info(f"API - Deleting poster cache for Show <s{show_id}>")

    async with state.acquire_db() as con:
        await con.execute(
            """
            UPDATE
                kitsu_info
            SET
                cached_poster_url = NULL
            WHERE
                show_id = ?;
        """,
            (show_id,),
        )


@api_router.get("/webhooks/{base_id}/valid")
async def webhook_is_valid(state: StateDep, base_id: int) -> Success[bool]:
    """Check if a Webhook is valid with the service it is for."""
    logger.info(f"API - Checking webhook validity for webhook ID {base_id}")

    webhook = await WebhookBase.from_id(state, base_id)
    if webhook is None:
        return Success(result=False)

    return Success(result=await webhook.is_valid())


@api_router.post("/account/change-password")
async def change_password(state: StateDep, user: DenyReadonlyDep, body: ChangePasswordRequest) -> Success[bool]:
    hasher = PasswordHasher()
    async with state.acquire_db() as con:
        user_data = await con.fetchone(
            """
            SELECT password_hash, username FROM users WHERE id = ?;
            """,
            user.id,
        )
        if not user_data:
            raise APIError(status.HTTP_404_NOT_FOUND, "User not found.")

        try:
            hasher.verify(user_data["password_hash"], body.current_password)
        except VerifyMismatchError as e:
            raise APIError(status.HTTP_400_BAD_REQUEST, "Current password is incorrect.") from e

        new_hash = hasher.hash(body.new_password)
        await con.execute(
            """
            UPDATE users SET password_hash=? WHERE id=?;
            """,
            new_hash,
            user.id,
        )

    return Success(result=True)


# "/webhooks/{base_id}/valid" and the show-scoped webhook routes are registered
# ahead of the generic base-webhook router so they resolve first.
for _router in (
    shows_router,
    show_entries_router,
    entries_router,
    webhooks_router,
    webhookbase_router,
    seen_releases_router,
    nyaa_router,
    libraries_router,
):
    api_router.include_router(_router)
