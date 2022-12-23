from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

    app: TsundokuApp
else:
    from quart import current_app as app

from tsundoku import __version__ as current_version
from tsundoku.utils import compare_version_strings


logger = logging.getLogger("tsundoku")

REQUEST_URL = "https://api.github.com/repos/{owner}/{repository}/releases/latest"


@dataclass
class UpdateInformation:
    """Information about a new release."""

    version: str
    url: str


async def check_for_updates() -> Optional[UpdateInformation]:
    headers = {"accept": "application/vnd.github+json"}

    url = REQUEST_URL.format(owner="tylergibbs2", repository="Tsundoku")
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
        return UpdateInformation(version, data["html_url"])

    logger.info("Update check: No new version is available.")
