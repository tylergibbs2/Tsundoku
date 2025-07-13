from pathlib import Path
import re

VERSION_RE = re.compile(r"version = \"(.+)\"")
PROJECT_FILE = Path(__file__).parent.parent / "pyproject.toml"


version = VERSION_RE.search(PROJECT_FILE.read_text())
if version is None:
    raise RuntimeError("Failed to determine application version")


__version__ = version.group(1)
