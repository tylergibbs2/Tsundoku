class Nyaa:
    def __init__(self, app):
        """
        Change 'self.url' and 'self.name' to be the URL 
        and name of the desired RSS feed to parse.
        """
        self.name = "nyaa.si"
        self.url = "https://nyaa.si/?page=rss"

        self.app = app

    def get_link_location(self, item):
        return item["link"]

    def ignore_logic(self, item):
        category = item["nyaa_category"]
        if category != "Anime - English-translated":
            return False


def setup(app):
    return Nyaa(app)
