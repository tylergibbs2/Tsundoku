class Nyaa:
    def __init__(self):
        """
        Change 'self.url' to be the URL of the desired
        RSS feed to parse.
        """
        self.url = "https://nyaa.si/?page=rss"

    def get_link_location(self, item):
        """
        Beginning from the <item> object, direct the
        script to where to find either:
        a.) the magnet URL
        b.) the torrent file

        Either of these two options will be parsed correctly
        by Tsundoku. If any manipulation needs to take place,
        please do that here.
        """
        return item["link"]

def setup():
    return Nyaa()
