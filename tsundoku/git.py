import logging
import subprocess

from tsundoku.config import get_config_value

# Git run command inspired by Tautulli's version check code!
# https://github.com/Tautulli/Tautulli/blob/master/plexpy/versioncheck.py


logger = logging.getLogger("tsundoku")


def run(args: str):
    git_loc = get_config_value("Tsundoku", "git_path")
    cmd = f"{git_loc} {args}"

    output = err = None

    try:
        logger.debug(f"Trying to execute '{cmd}' with shell")
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True
        )
        output, err = p.communicate()
        output = output.strip().decode()

        logger.debug(f"Git output: {output}")
    except OSError:
        logger.debug(f"Command failed: {cmd}")
    else:
        if "not found" in output or "not recognized as an internal or external command" in output:
            logger.debug(f"Unable to find git with command {cmd}")
        elif "fatal: " in output or err:
            logger.error("Git returned bad info. Bad git installation?")

    return output, err