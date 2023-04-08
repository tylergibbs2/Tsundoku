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

# display size -> bytes
VALID_MINIMUM_FILE_SIZES = {
    "any": 0,
    "250mb": 250 * 1e6,
    "500mb": 500 * 1e6,
    "750mb": 750 * 1e6,
    "1000mb": 1000 * 1e6,
    "1250mb": 1250 * 1e6,
    "1500mb": 1500 * 1e6,
}

VALID_ENCODERS = {"--enable-libx264": "libx264", "--enable-libx265": "libx265"}

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
LOGGING_FILE_NAME = "tsundoku.log"

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
