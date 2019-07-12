import configparser
import typing


config = configparser.ConfigParser()
config.read("config.ini")


def get_config_value(section: str, value: str) -> typing.Union[int, str]:
    """
    Returns a specified value from the config.ini file.

    All values retrieved are strings. If the string is composed
    entirely of integers, the value will be automatically casted
    to an integer.

    Parameters
    ----------
    section: str
        The section to retrieve the value from.
    value: str
        The specified value to retrieve.

    Returns
    -------
    typing.Union[int, str]
        The requested value.

    Raises
    ------
    KeyError
        The specified section or value does not exist.
    """
    try:
        section = config[section]
    except KeyError:
        raise KeyError("The specified section does not exist.")

    try:
        return int(section[value]) if section[value].isdigit() else section[value]
    except KeyError:
        raise KeyError("The specified value does not exist.")
