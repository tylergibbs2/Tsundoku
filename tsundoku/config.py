import configparser
import json
from typing import Any


config = configparser.ConfigParser()
config.read("config.ini")


def get_config_value(section: str, value: str) -> Any:
    """
    Returns a specified value from the config.ini file.

    All values retrieved are strings. If the value contains
    non-string elements, they will be casted using json.loads.

    Parameters
    ----------
    section: str
        The section to retrieve the value from.
    value: str
        The specified value to retrieve.

    Returns
    -------
    Any
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
        value = section[value]
    except KeyError:
        raise KeyError("The specified value does not exist.")

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value
