from typing import Any, Optional

import anitopy


class SubsPlease:
    def __init__(self, app: Any) -> None:
        """
        Change 'self.url' and 'self.name' to be the URL
        and name of the desired RSS feed to parse.
        """
        self.name = "SubsPlease"
        self.url = "https://subsplease.org/rss/?t&r=1080"
        self.version = "1.0.0"

        self.app = app

    def get_show_name(self, file_name: str) -> Optional[str]:
        """
        Using the `file_name` argument, you must parse
        the file name in order to get the name of the show.

        Failure to do so will result in incorrect matching.
        """
        parsed = anitopy.parse(file_name)
        if parsed is None:
            return None

        return parsed["anime_title"]

    def get_episode_number(self, file_name: str) -> Optional[int]:
        """
        Using the `file_name` argument, you must parse
        the file name in order to get the episode of the release.

        Failure to do so will result in incorrect matching.

        Returning `None` will stop the matching.
        """
        parsed = anitopy.parse(file_name)
        if parsed is None:
            return None

        if "anime_type" in parsed.keys():
            return None

        extra_info = parsed.get("release_information", "")
        if "batch" in extra_info.lower():
            return None

        try:
            episode = parsed["episode_number"]
        except KeyError:
            return None

        try:
            return int(episode)
        except (ValueError, TypeError):
            return None


def setup(app: Any) -> SubsPlease:
    return SubsPlease(app)
