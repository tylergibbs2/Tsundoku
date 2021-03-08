class ParserError(Exception):
    """
    Represents a generic custom RSS parser error.
    """


class ParserNotFound(ParserError):
    """
    The custom RSS parser was not found.
    """


class ParserMissingSetup(ParserError):
    """
    The custom RSS parser is missing its setup function.
    """


class ParserFailed(ParserError):
    """
    Some error occurred when attempting to load the parser.
    """


class ParserMissingRequiredFunction(ParserError):
    """
    The custom RSS parser is missing a required function.
    """
