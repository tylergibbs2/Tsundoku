import os

from tsundoku.git import UpdateInformation


class Flags:
    IS_DOCKER: bool = bool(os.getenv("IS_DOCKER"))
    IS_DEBUG: bool = bool(os.getenv("IS_DEBUG"))
    IS_FIRST_LAUNCH: bool = False
    DL_CLIENT_CONNECTION_ERROR: bool = False
    UPDATE_INFO: UpdateInformation | None = None
    LOCALE: str = "en"

    #: Development only. When set, torrent locations are routed through a
    #: local mirror that swaps real content for synthetic content of the same
    #: shape, so a real magnet can be pasted in and downloaded from a local
    #: swarm instead of the internet. Off unless explicitly pointed somewhere;
    #: see integration/README.md.
    TORRENT_MIRROR_URL: str | None = os.getenv("TORRENT_MIRROR_URL") or None

    def __repr__(self) -> str:
        return f"<Flags IS_DOCKER={self.IS_DOCKER}, IS_DEBUG={self.IS_DEBUG}, IS_FIRST_LAUNCH={self.IS_FIRST_LAUNCH}, DL_CLIENT_CONNECTION_ERROR={self.DL_CLIENT_CONNECTION_ERROR}, LOCALE={self.LOCALE}, TORRENT_MIRROR_URL={self.TORRENT_MIRROR_URL}>"
