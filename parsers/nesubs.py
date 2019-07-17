import re

class NeSubs:
    def __init__(self, app):
        """
        Change 'self.url' and 'self.name' to be the URL 
        and name of the desired RSS feed to parse.
        """
        self.name = "NeSubs"
        self.url = "https://www.shanaproject.com/feeds/subber/NeSubs/"

        self.app = app

    def get_show_name(self, file_name: str) -> str:
        """
        Using the `file_name` argument, you must parse
        the file name in order to get the name of the show.

        Failure to do so will result in incorrect matching.
        """
        pattern = re.compile(r"\[NeSubs\] (.+) - .*(\d+)")
        match = re.match(pattern, file_name)

        return match.group(1)

    def get_episode_number(self, file_name: str) -> int:
        """
        Using the `file_name` argument, you must parse
        the file name in order to get the episode of the release.

        Failure to do so will result in incorrect matching.
        """
        pattern = re.compile(r"\[NeSubs\] (.+) - .*(\d+)")
        match = re.match(pattern, file_name)

        return int(match.group(2))

    def get_link_location(self, item: dict) -> str:
        """
        Optional

        Beginning from the <item> object, direct the
        script to where to find either:
        a.) the magnet URL
        b.) the torrent file

        Either of these two options will be parsed correctly
        by Tsundoku. If any manipulation needs to take place,
        please do that here.

        If this method does not exist, item["link"] will be used.
        """
        return item["guid"]

    def get_file_name(self, item: dict) -> str:
        """
        Optional

        Beginning from the <item> object, direct the
        script to where to find the name of the item.

        If this method does not exist, item["title"] will be used.
        """
        return item["description"]


def setup(app):
    return NeSubs(app)
