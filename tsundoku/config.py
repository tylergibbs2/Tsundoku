import configparser
import json
import os
from typing import Any

config = configparser.ConfigParser()

if os.getenv("IS_DOCKER"):
    fp = "data/config.ini"
else:
    fp = "config.ini"

config.read(fp)


def get_config_value(section: str, value: str, default: Any = None) -> Any:
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
        found_section: Any = config[section]
    except KeyError:
        return default

    try:
        found_value: str = found_section[value]
    except KeyError:
        return default

    try:
        return json.loads(found_value)
    except json.JSONDecodeError:
        return found_value


def set_config_value(section: str, value: str, data: Any) -> None:
    """
    Set a specified value to the config.ini file.

    All values will be casted using json.dumps.

    Parameters
    ----------
    section: str
        The section to set the value in.
    value: str
        The value to set.
    data: Any
        The data to write.

    Returns
    -------
    None
    """
    config.read(fp)
    config.set(section, value, json.dumps(data))

    with open(fp, "w") as f:
        config.write(f)
