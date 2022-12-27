import os
from pathlib import Path


VALID_SPEEDS = (
    "ultrafast",
    "superfast",
    "veryfast",
    "faster",
    "fast",
    "medium",
    "slow",
    "slower",
    "veryslow",
)

VALID_SERVICES = ("discord", "slack", "custom")

VALID_TRIGGERS = (
    "downloading",
    "downloaded",
    "renamed",
    "moved",
    "completed",
    "failed",
)

VALID_RESOLUTIONS = (
    "480p",
    "720p",
    "1080p",
    "4k",
)

STATUS_HTML_MAP = {
    "current": "<span class='img-overlay-span tag is-success noselect'>{}</span>",
    "finished": "<span class='img-overlay-span tag is-danger noselect'>{}</span>",
    "tba": "<span class='img-overlay-span tag is-warning noselect'>{}</span>",
    "unreleased": "<span class='img-overlay-span tag is-info noselect'>{}</span>",
    "upcoming": "<span class='img-overlay-span tag is-primary noselect'>{}</span>",
}

DATABASE_FILE_NAME = "tsundoku.db"

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
