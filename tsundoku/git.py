import asyncio
import logging
import os
import sys
from typing import TYPE_CHECKING, Any, Optional, Tuple

if TYPE_CHECKING:
    app: Any
else:
    from quart import current_app as app

from tsundoku.config import get_config_value
from tsundoku.database import migrate

# Git run command inspired by Tautulli's version check code!
# https://github.com/Tautulli/Tautulli/blob/master/plexpy/versioncheck.py


logger = logging.getLogger("tsundoku")


async def run(args: str) -> Tuple[str, Optional[bytes]]:
    git_loc = get_config_value("Tsundoku", "git_path")
    cmd = f"{git_loc} {args}"

    stdout: Optional[bytes] = None
    stderr: Optional[bytes] = None

    try:
        logger.debug(f"Git: Trying to execute `{cmd}` with shell")
        proc = await asyncio.subprocess.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, stderr = await proc.communicate()

        output_text = stdout.strip().decode()

        logger.debug(f"Git: output: {output_text}")
    except OSError:
        logger.debug(f"Git: command failed: {cmd}")
    else:
        if "not found" in output_text or "not recognized as an internal or external command" in output_text:
            logger.debug(f"Git: Unable to find executable with command {cmd}")
        elif "fatal: " in output_text or stderr:
            logger.error("Git: Returned bad info. Bad installation?")

    return output_text, stderr


async def update() -> None:
    """
    Performs a "git pull" to update the local
    Tsundoku to the latest GitHub version.
    """
    if not app.update_info:
        return

    logger.info("Tsundoku is updating...")

    out, _ = await run("pull --ff-only")

    if not out:
        logger.error("Git: Unable to download latest version")
        return

    for line in out.split("\n"):
        if "Already up-to-date." in line or "Already up to date." in line:
            logger.info("Git: No update available")
            return
        elif line.endswith(("Aborting", "Aborting.")):
            logger.error(f"Git: Unable to update, {line}")
            return

    proc = await asyncio.subprocess.create_subprocess_shell(
        f"{sys.executable} -m pip install -r requirements.txt"
    )
    await proc.wait()

    await migrate()

    app.update_info = []


async def check_for_updates() -> None:
    """
    Checks for updates from GitHub.

    If commit is newer, prompt for an update.
    """
    is_docker = os.environ.get("IS_DOCKER", False)
    if is_docker:
        return

    out, e = await run("fetch")
    out, e = await run("rev-list --format=oneline HEAD..origin/master")
    if not out or e:
        return

    commits = []
    for commit in out.split("\n"):
        hash_ = commit.split()[0]
        message = " ".join(commit.split()[1:])
        commits.append([hash_, message])

    if commits:
        app.update_info = commits
