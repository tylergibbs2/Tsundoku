class PollerError(Exception):
    """
    Represents a generic exception with the Poller class.
    """
    pass


class InvalidPollerInterval(PollerError):
    """
    The configured interval for polling is invalid.
    """
    pass
