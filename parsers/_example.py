class Example:
    def __init__(self, app):
        """
        Change 'self.url' and 'self.name' to be the URL 
        and name of the desired RSS feed to parse.
        """
        self.name = "Example - this is entirely aesthetic"
        self.url = "http://www.example.com/rss"

        self.app = app

    def get_show_name(self, file_name: str) -> str:
        """
        Using the `file_name` argument, you must parse
        the file name in order to get the name of the show.

        Failure to do so will result in incorrect matching.
        """
        return file_name

    def get_episode_number(self, file_name: str) -> int:
        """
        Using the `file_name` argument, you must parse
        the file name in order to get the episode of the release.

        Failure to do so will result in incorrect matching.
        """
        return 0

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
        return item["link"]

    def get_file_name(self, item: dict) -> str:
        """
        Optional

        Beginning from the <item> object, direct the
        script to where to find the name of the item.

        If this method does not exist, item["title"] will be used.
        """
        return item["title"]

    def ignore_logic(self, item: dict) -> bool:
        """
        Optional

        This is the first function a parser runs.

        If this returns False, the item will instantly
        be ignored by Tsundoku. Any other return value
        will continue operation as normal.
        """
        pass


def setup(app):
    return Example(app)
