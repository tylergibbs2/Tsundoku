import os


class Flags:
    IS_DOCKER: bool = bool(os.getenv("IS_DOCKER"))
    IS_DEBUG: bool = bool(os.getenv("IS_DEBUG"))
    IS_FIRST_LAUNCH: bool = False
