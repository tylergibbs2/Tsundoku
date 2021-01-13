import anitopy


class SubsPlease:
    def __init__(self, app):
        """
        Change 'self.url' and 'self.name' to be the URL
        and name of the desired RSS feed to parse.
        """
        self.name = "SubsPlease"
        self.url = "https://subsplease.org/rss/?t&r=1080"
        self.version = "1.0.0"

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

        Returning `None` will stop the matching.
        """
        parsed = anitopy.parse(file_name)

        if "anime_type" in parsed.keys():
            return

        extra_info = parsed.get("release_information", "")
        if "batch" in extra_info.lower():
            return

        try:
            episode = parsed["episode_number"]
        except KeyError:
            return

        try:
            return int(episode)
        except (ValueError, TypeError):
            return


def setup(app):
    return SubsPlease(app)
