import re

import anitopy


class EraiRaws:
    def __init__(self, app):
        """
        Change 'self.url' and 'self.name' to be the URL
        and name of the desired RSS feed to parse.
        """
        self.name = "Erai-raws"
        self.url = "https://nyaa.si/?page=rss&u=Erai-raws"

        self.app = app

    def get_show_name(self, file_name: str) -> str:
        """
        Using the `file_name` argument, you must parse
        the file name in order to get the name of the show.

        Failure to do so will result in incorrect matching.
        """
        parsed = anitopy.parse(file_name)

        return parsed["anime_title"]

    def get_episode_number(self, file_name: str) -> int:
        """
        Using the `file_name` argument, you must parse
        the file name in order to get the episode of the release.

        Failure to do so will result in incorrect matching.
        """
        parsed = anitopy.parse(file_name)

        try:
            return int(parsed["episode_number"])
        except ValueError:
            return 0

    def ignore_logic(self, item: dict) -> bool:
        """
        Optional

        This is the first function a parser runs.

        If this returns False, the item will instantly
        be ignored by Tsundoku. Any other return value
        will continue operation as normal.
        """
        parsed = anitopy.parse(item["title"])

        title = parsed.get("anime_title")
        episode = parsed.get("episode_number")
        resolution = parsed.get("video_resolution")
        if title is None or episode is None or resolution is None:
            return False
        elif resolution != "1080p":
            return False


def setup(app):
    return EraiRaws(app)
