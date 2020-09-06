import asyncio
from contextlib import suppress
from hypercorn.utils import restart
import logging
import os
import subprocess
import sys
import traceback

import asyncpg
from yoyo import get_backend, read_migrations
from quart import current_app as app

from tsundoku.config import get_config_value

# Git run command inspired by Tautulli's version check code!
# https://github.com/Tautulli/Tautulli/blob/master/plexpy/versioncheck.py


logger = logging.getLogger("tsundoku")


def run(args: str):
    git_loc = get_config_value("Tsundoku", "git_path")
    cmd = f"{git_loc} {args}"

    output = err = None

    try:
        logger.debug(f"Git: Trying to execute '{cmd}' with shell")
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True
        )
        output, err = p.communicate()
        output = output.strip().decode()

        logger.debug(f"Git: output: {output}")
    except OSError:
        logger.debug(f"Git: command failed: {cmd}")
    else:
        if "not found" in output or "not recognized as an internal or external command" in output:
            logger.debug(f"Git: Unable to find executable with command {cmd}")
        elif "fatal: " in output or err:
            logger.error("Git: Returned bad info. Bad installation?")

    return output, err


async def migrate():
    host = get_config_value("PostgreSQL", "host")
    port = get_config_value("PostgreSQL", "port")
    user = get_config_value("PostgreSQL", "user")
    db_password = get_config_value("PostgreSQL", "password")
    database = get_config_value("PostgreSQL", "database")

    try:
        con = await asyncpg.connect(
            host=host,
            user=user,
            password=db_password,
            port=port,
            database=database
        )
    except asyncpg.InvalidCatalogNameError:
        sys_con = await asyncpg.connect(
            host=host,
            user=user,
            password=db_password,
            port=port,
            database="template1"
        )
        await sys_con.execute(f"""
            CREATE DATABASE "{database}" OWNER "{user}";
        """)
        await sys_con.close()

    con = await asyncpg.connect(
        host=host,
        user=user,
        password=db_password,
        port=port,
        database=database
    )

    await con.close()

    backend = get_backend(f"postgres://{user}:{db_password}@{host}:{port}/{database}")
    migrations = read_migrations("migrations")

    logger.info("Applying database migrations...")
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))
    logger.info("Database migrations applied.")


async def update():
    """
    Performs a "git pull" to update the local
    Tsundoku to the latest GitHub version.
    """
    if not app.update_info:
        return

    logger.info("Tsundoku is updating...")

    out, e = run("pull --ff-only")

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

    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    await migrate()

    app.update_info = []


def check_for_updates():
    """
    Checks for updates from GitHub.

    If commit is newer, prompt for an update.
    """
    out, e = run("fetch")
    out, e = run("rev-list --format=oneline HEAD..origin/master")
    if not out or e:
        return

    commits = []
    for commit in out.split("\n"):
        hash_ = commit.split()[0]
        message = " ".join(commit.split()[1:])
        commits.append([hash_, message])

    if commits:
        app.update_info = commits
