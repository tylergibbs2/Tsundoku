import os
import platform
from urllib.parse import quote

import distro
from user_agents import parse

from tsundoku import __version__

BUG_REPORT = """
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Desktop (please complete the following information, if relevant):**
 - OS: {ua.os.family} {ua.os.version_string}
 - Browser: {ua.browser.family} {ua.browser.version_string}
 - Device: {ua.device.model}

**Software**
 - Tsundoku version: {version}
 - Tsundoku Python version: {python_version}
 - Tsundoku host system: {host_system}
 - Docker?: {docker}

**Additional context**
Add any other context about the problem here.
"""


def get_issue_url(issue_type: str, useragent: str) -> str:
    repo_owner = os.getenv("GITHUB_REPO_OWNER", "tylergibbs2")
    repo_name = os.getenv("GITHUB_REPO_NAME", "Tsundoku")

    if issue_type == "bug":
        parsed_ua = parse(useragent)
        linux_version = " ".join(distro.linux_distribution()).split()

        ctx = {
            "docker": bool(os.getenv("IS_DOCKER")),
            "python_version": platform.python_version(),
            "host_system": linux_version or platform.platform(),
            "version": __version__,
            "ua": parsed_ua,
        }

        body = quote(BUG_REPORT.format(**ctx))

        return (
            f"https://github.com/{repo_owner}/{repo_name}/issues/new?labels=bug&title=&body="
            + body
        )

    return f"https://github.com/{repo_owner}/{repo_name}/issues/new?labels=feature%20request&template=feature_request.md"
