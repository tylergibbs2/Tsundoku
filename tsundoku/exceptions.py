class ParserError(Exception):
    """
    Represents a generic custom RSS parser error.
    """
    pass


class ParserNotFound(ParserError):
    """
    The custom RSS parser was not found.
    """
    pass


class ParserMissingSetup(ParserError):
    """
    The custom RSS parser is missing its setup function.
    """
    pass


class ParserFailed(ParserError):
    """
    Some error occurred when attempting to load the parser.
    """
    pass


class ParserMissingRequiredFunction(ParserError):
    """
    The custom RSS parser is missing a required function.
    """
    pass