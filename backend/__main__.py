"""
Kultur Klash website backend
"""

import logging
import sys

import click

from . import __version__
from .config import ConfigError, init_logging
from .server import Server

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(__version__)
def main() -> None:
    """
    The Kultur Klash site and web apps backend.
    """


@main.command()
def start() -> None:
    """
    Starts the backend API.
    """
    try:
        _start_wrapper()
    except ConfigError as e:
        print(e)
        sys.exit(1)


def _start_wrapper() -> None:
    init_logging()
    logger.info("Starting Backend.")
    server = Server()
    server.start()


if __name__ == "__main__":
    main()
