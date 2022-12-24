import os


class Flags:
    IS_DOCKER: bool = bool(os.getenv("IS_DOCKER"))
    IS_DEBUG: bool = bool(os.getenv("IS_DEBUG"))
    IS_FIRST_LAUNCH: bool = False
    DL_CLIENT_CONNECTION_ERROR: bool = False
    LOCALE: str = "en"

    def __repr__(self) -> str:
        return f"<Flags IS_DOCKER={self.IS_DOCKER}, IS_DEBUG={self.IS_DEBUG}, IS_FIRST_LAUNCH={self.IS_FIRST_LAUNCH}, DL_CLIENT_CONNECTION_ERROR={self.DL_CLIENT_CONNECTION_ERROR}, LOCALE={self.LOCALE}>"
