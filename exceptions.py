class ParserNotFound(Exception):
    """
    The custom RSS parser was not found.
    """
    pass


class ParserMissingSetup(Exception):
    """
    The custom RSS parser is missing it's setup function.
    """
    pass


class ParserFailed(Exception):
    """
    Some error occurred when attempting to load the parser.
    """
    pass


class DelugeAuthorizationError(Exception):
    """
    Represents a Deluge authorization error.
    """
    pass
