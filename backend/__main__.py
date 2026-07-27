"""
Kultur Klash website backend
"""

import asyncio
import logging
import sys
from typing import Awaitable, Callable, ParamSpec

import click

from . import __version__, config
from .database import Database
from .error import BaseError
from .server import Server

logger = logging.getLogger(__name__)

P = ParamSpec("P")


@click.group()
@click.version_option(__version__)
def main() -> None:
    """
    The Ticket Klash web apps backend.
    """
    config.init_logging()


def _cmd_wrapper(
    function: Callable[P, None], *args: P.args, **kwargs: P.kwargs
) -> None:
    """
    Wraps a cmd and catches any errors that may happen
    to display them nicely.
    """
    try:
        function(*args, **kwargs)
    except BaseError as e:
        print("===", e, "===")
        sys.exit(1)


async def _async_cmd_wrapper(
    function: Callable[P, Awaitable[None]], *args: P.args, **kwargs: P.kwargs
) -> None:
    """
    Wraps a cmd, executes it asyncly and catches any errors that may happen
    to display them nicely.
    """
    try:
        await function(*args, **kwargs)
    except BaseError as e:
        print("===", e, "===")
        sys.exit(1)


@main.command()
def start() -> None:
    """
    Starts the backend API.
    """
    _cmd_wrapper(_start)


def _start() -> None:
    logger.info("Starting Backend.")
    server = Server()
    server.start()


@main.group()
def database() -> None:
    """
    Commands to manipulate the database.
    """


@database.command(name="init")
@click.option("--username")
@click.option("--db-name")
def init_db(username: str | None, db_name: str | None) -> None:
    """Initilizes a new database on a postgres instance."""
    asyncio.run(_async_cmd_wrapper(_init_db, username, db_name))


async def _init_db(username: str | None, db_name: str | None) -> None:
    config.IGNORE_MISSING_DEFAULTS = True
    db = Database()
    await db.init(username, db_name)


if __name__ == "__main__":
    main()
