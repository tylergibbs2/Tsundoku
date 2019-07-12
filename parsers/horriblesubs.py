class HorribleSubs:
    def __init__(self):
        """
        Change 'self.url' and 'self.name' to be the URL 
        and name of the desired RSS feed to parse.
        """
        self.name = "HorribleSubs"
        self.url = "http://www.horriblesubs.info/rss.php?res=720"

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
    return HorribleSubs()
