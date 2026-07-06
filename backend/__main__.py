"""
Kultur Klash website backend
"""

import logging

import click

from . import __version__
from .config import init_logging

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
    init_logging()
    logger.info("Starting Backend.")


if __name__ == "__main__":
    main()
