class HorribleSubs:
    def __init__(self, app):
        self.name = "HorribleSubs"
        self.url = "http://www.horriblesubs.info/rss.php?res=720"

        self.app = app

    def get_link_location(self, item):
        return item["link"]
        

def setup(app):
    return HorribleSubs(app)
