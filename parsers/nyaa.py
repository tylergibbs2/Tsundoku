class Nyaa:
    def __init__(self, app):
        self.name = "nyaa.si"
        self.url = "https://nyaa.si/?page=rss&c=1_2"

        self.app = app


def setup(app):
    return Nyaa(app)
