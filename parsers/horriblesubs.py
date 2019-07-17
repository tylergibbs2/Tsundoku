import re

class HorribleSubs:
    def __init__(self, app):
        """
        Change 'self.url' and 'self.name' to be the URL 
        and name of the desired RSS feed to parse.
        """
        self.name = "HorribleSubs"
        self.url = "http://www.horriblesubs.info/rss.php?res=720"

        self.app = app

    def get_show_name(self, file_name: str) -> str:
        """
        Using the `file_name` argument, you must parse
        the file name in order to get the name of the show.

        Failure to do so will result in incorrect matching.
        """
        pattern = re.compile(r"\[HorribleSubs\] (.+) -[.\s]*(\d+)")
        match = re.match(pattern, file_name)

        return match.group(1)

    def get_episode_number(self, file_name: str) -> int:
        """
        Using the `file_name` argument, you must parse
        the file name in order to get the episode of the release.

        Failure to do so will result in incorrect matching.
        """
        pattern = re.compile(r"\[HorribleSubs\] (.+) -[.\s]*(\d+)")
        match = re.match(pattern, file_name)

        return int(match.group(2))


def setup(app):
    return HorribleSubs(app)
