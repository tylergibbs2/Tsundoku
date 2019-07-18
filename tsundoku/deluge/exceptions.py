class DelugeError(Exception):
    """
    Represents a generic Deluge error.
    """
    pass


class DelugeAuthorizationError(DelugeError):
    """
    Represents a Deluge authorization error.
    """
    pass
