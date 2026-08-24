"""
Manages logging and configuration.
Only reads ENV variables.
Env variables are ALL CAPS and structured as followes:
TF_{SECTION}_{OPTION}
"""

import logging
import os
from getpass import getpass
from ipaddress import IPv4Address, IPv6Address, ip_address
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .error import BaseError

IGNORE_MISSING_DEFAULTS = False


class ConfigError(BaseError):
    """A configuration error of some kind."""


class RequiredOption(ConfigError):
    """A required option, that wasn't set."""


class BadOptionValue(ConfigError):
    """A setting was given a bad value."""


def _get_env_var_name(section: str, option: str) -> str:
    section = section.replace("-", "_").replace(".", "_")
    option = option.replace("-", "_")
    return f"TF_{section.upper()}_{option.upper()}"


def _get_from_env(section: str, option: str) -> str | None:
    env_var = _get_env_var_name(section, option)
    return os.environ.get(env_var)


def get(section: str, option: str, default: str | None = None) -> str:
    """
    Retrieves a value from the env variables.
    If the default value is not set, it throws an error if no value was found.
    """
    env_var_value = _get_from_env(section, option)
    if env_var_value is not None:
        return env_var_value

    if default is None:
        if IGNORE_MISSING_DEFAULTS:
            return ""

        raise RequiredOption(
            f"Option '{_get_env_var_name(section, option)}' requries a value."
        )

    return default


def get_int(section: str, option: str, default: int | None = None) -> int:
    """
    Tries to retrieve a config option as an int.
    Uses config.get and type coersion internally.
    """
    if default is not None:
        str_default: str | None = str(default)
    else:
        str_default = None

    try:
        value = get(section, option, str_default)
        return int(value)
    except ValueError as e:
        raise BadOptionValue(
            f"Option '{_get_env_var_name(section, option)}' is not an integer. "
            f'(Current value:"{value}")'
        ) from e


def _str_to_bool(value: str) -> bool | None:
    """
    Tries to turn a string in to a boolean value.

    True values are '1', 'yes', 'y', 'true' and 'on'.
    False values are '0', 'no', 'n', 'false' and 'off'.
    These are not case sensitive
    """
    if value.lower() in ["1", "yes", "true", "on"]:
        return True

    if value.lower() in ["0", "no", "false", "off"]:
        return False

    return None


def get_bool(section: str, option: str, default: bool | None = None) -> bool:
    """
    Tries to retrieve a config option as a boolean value.
    True values are '1', 'yes', 'true' and 'on'.
    False values are '0', 'no', 'false' and 'off'.
    These values are not case sensitive.
    Uses config.get internally.
    """
    if default is not None:
        str_default: str | None = str(default)
    else:
        str_default = None

    value = get(section, option, str_default)
    boolean_value = _str_to_bool(value)
    if boolean_value is not None:
        return boolean_value

    raise BadOptionValue(
        f"Option '{_get_env_var_name(section, option)}' is not an accepted boolean value. "
        f'(Current value:"{value}")'
    )


IpAddress = IPv4Address | IPv6Address


def get_ip(
    section: str,
    option: str,
    default: IpAddress | None = None,
    family: type[IpAddress] | None = None,
) -> IpAddress:
    """
    Gets the value like any other get, then tries to convert it to an IpAdress
    and the required family if the family is not None.
    """
    if default is not None:
        str_default = str(default)
    else:
        str_default = None

    str_value = get(section, option, default=str_default)

    if str_value is not None:
        try:
            value = ip_address(str_value)
        except ValueError as e:
            raise BadOptionValue(
                f"Option '{_get_env_var_name(section, option)}' is not a valid IP address."
            ) from e

        if family is not None and not isinstance(value, family):
            raise BadOptionValue(
                f"Option '{_get_env_var_name(section, option)}' is not the right ipaddres family."
            )

        return value

    if default is not None:
        return default

    raise RequiredOption(f"Option {option} in section {section} requries a value.")


def get_multichoice(
    section: str, option: str, choices: list[str], default: str | None = None
) -> str:
    """
    Does a normal config.get and then matches the returned value to the list of choices.
    Matching is bypassed if the default value is returned.
    """
    value = get(section, option, default)

    if value == default:
        return value

    if value in choices:
        return value

    raise BadOptionValue(
        f"Option '{_get_env_var_name(section, option)}' has a bad value. "
        f"Possible values: [{','.join(choices)}]"
    )


def get_path(
    section: str,
    option: str,
    default: Path | None = None,
    absolute: bool = False,
    must_exist: bool = False,
) -> Path:
    """
    Tries to retrieve a config option as a pathlib.Path value.
    The 'absolute' and 'exists' parameters raise errors if the path is not
    absolute or does not exist, respectively.
    """
    if default is not None:
        str_default = str(default)
    else:
        str_default = None

    value = Path(get(section, option, str_default))
    if absolute and not value.absolute():
        raise BadOptionValue(
            f"Option '{_get_env_var_name(section, option)}' expects an absolute path. "
            f"(Current value: '{value}')"
        )

    if must_exist and not value.exists():
        raise BadOptionValue(
            f"Option '{_get_env_var_name(section, option)}' doesn't exist. "
            f"(Current value: '{value}')"
        )

    return value


def _init_access_logger(logging_dir: Path) -> None:
    access_handler = RotatingFileHandler(filename=logging_dir / "access.log")
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    access_logger = logging.getLogger("aiohttp.access")
    access_logger.handlers.clear()
    access_logger.addHandler(access_handler)
    access_logger.propagate = False


def init_logging() -> None:
    """
    Initialises the logging subsystem.
    Uses standard python logging.
    """
    section = "log"
    logger_format = get_multichoice(section, "format", ["json", "raw"], "raw")
    out = get_multichoice(section, "out", ["stdout", "file"], "stdout")
    level = getattr(
        logging,
        get_multichoice(
            section, "level", ["ERROR", "WARNING", "INFO", "DEBUG"], "INFO"
        ),
    )
    logging_dir = get_path(section, "path", Path("/var/log/tf-api"))

    if logger_format == "json":
        log_format = '{"time": %(asctime)s, "name": %(name)s, "level": %(levelname)s, "message" %(message)s}'
    else:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if out == "stdout":
        logging.basicConfig(
            format=log_format,
            level=level,
        )
    else:
        logging_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            format=log_format,
            level=level,
            filename=logging_dir / "server.log",
        )

    if get_bool("http", "log_access", False):
        logging_dir.mkdir(parents=True, exist_ok=True)
        _init_access_logger(logging_dir)


def get_input(prompt: str, default: str) -> str:
    """
    Wrapper around input() that returns a default if the answer was empty.
    Will add the default to the prompt and add a colon.
    """
    response = input(prompt + f"[{default}]: ")
    if response == "":
        return default
    return response


def get_pass(attempt: int = 0) -> str:
    """
    Gets and confirms a password before returning it.
    """
    pass_1 = getpass()
    pass_2 = getpass("Confirm Password: ")

    if pass_1 == pass_2:
        return pass_1

    if attempt < 3:
        print("\nPasswords didn't match, please try again.")
        return get_pass(attempt + 1)

    raise BaseError("Failed to confirm password too many times.")
