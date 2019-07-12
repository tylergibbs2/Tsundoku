class Example:
    def __init__(self, app):
        """
        Change 'self.url' and 'self.name' to be the URL 
        and name of the desired RSS feed to parse.
        """
        self.name = "Example - this is entirely aesthetic"
        self.url = "http://www.example.com/rss"

        self.app = app

    def get_link_location(self, item):
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

    def get_file_name(self, item):
        """
        Optional

        Beginning from the <item> object, direct the
        script to where to find the name of the file.

        If this method does not exist, item["title"] will be used.
        """
        return item["title"]

    def ignore_logic(self, item):
        """
        Optional

        If this returns False, the item will instantly
        be ignored by Tsundoku. Any other return value
        will continue operation as normal.
        """
        pass


def setup(app):
    return Example(app)
