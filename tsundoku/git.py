from dataclasses import dataclass
import logging
import os
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

    app = TsundokuApp()
else:
    from quart import current_app as app

from tsundoku import __version__ as current_version
from tsundoku.config import GeneralConfig
from tsundoku.utils import compare_version_strings


logger = logging.getLogger("tsundoku")

REQUEST_URL = "https://api.github.com/repos/{owner}/{repository}/releases/latest"


@dataclass
class UpdateInformation:
    """Information about a new release."""

    version: str
    url: str


async def check_for_updates() -> Optional[UpdateInformation]:
    config = await GeneralConfig.retrieve(app)
    if not config.get("update_do_check", False):
        logger.info("Update checks disabled by configuration, skipping.")
        return

    headers = {"accept": "application/vnd.github+json"}

    repo_owner = os.getenv("GITHUB_REPO_OWNER", "tylergibbs2")
    repo_name = os.getenv("GITHUB_REPO_NAME", "Tsundoku")

    logger.info(
        f"Update check: Checking for updates at github.com/{repo_owner}/{repo_name}"
    )

    url = REQUEST_URL.format(owner=repo_owner, repository=repo_name)
    async with app.session.get(url, headers=headers) as resp:
        data = await resp.json()

    if resp.status == 404:
        logger.error("Update check: Could not find repository on GitHub.")
        return None
    elif resp.status != 200:
        logger.error("Update check: Could not connect to GitHub.")
        return None

    if "name" not in data:
        logger.error("Update check: Could not find release name.")
        return None

    version = data["name"]
    logger.debug(f"Update check: Latest version on GitHub is {version}.")

    if compare_version_strings(version, current_version) > 0:
        if "html_url" not in data:
            logger.error("Update check: Could not find release URL.")
            return None

        logger.info(f"Update check: New version {version} is available.")
        app.flags.UPDATE_INFO = UpdateInformation(version, data["html_url"])
        return app.flags.UPDATE_INFO

    logger.info("Update check: No new version is available.")
