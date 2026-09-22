"""
Kultur Klash website backend
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Awaitable, Callable, ParamSpec

import click

from . import DEVMODE, PRODUCTION, __version__, config
from .backend import password_util
from .backend.database import SCHEMA_VERSION, Database
from .backend.object_def_table import DEF_TABLE
from .error import BaseError
from .server import Server

logger = logging.getLogger(__name__)

P = ParamSpec("P")


@click.group()
@click.version_option(__version__)
def main() -> None:
    """
    The Ticket Flash web app backend.
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
        print("=== ERROR:", e, "===")
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
        print("=== ERROR:", e, "===")
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


@main.command()
@click.option("--db-username")
@click.option("--db-name")
def init(db_username: str | None, db_name: str | None) -> None:
    "Initialize the application for use."
    asyncio.run(_async_cmd_wrapper(_init, db_username, db_name))


async def _init(db_username: str | None, db_name: str | None) -> None:
    print("Generating secrets and initializing database")
    response = config.get_input("Initialize database? (Y/N)", "y")
    if response.lower() != "n":
        await _init_db(db_username, db_name)


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


@main.group()
def peppers() -> None:
    """
    Commands to manipulate the password systems peppers.
    """


@database.command()
def rotate_peppers() -> None:
    """Generate a new pepper for the login system. This is a security measure."""
    _cmd_wrapper(_rotate_peppers)


def _rotate_peppers() -> None:
    config.get_config_dir().mkdir()
    password_util.rotate_pepper()
    pepper = password_util.PEPPER_STRUCT.get_current_pepper()
    print("Generating new pepper")
    password_util.print_pepper(pepper)
    if config.get_input("Clean up old peppers? [Y/n]", "Y").lower() == "y":
        password_util.clean()


@main.group()
def dev() -> None:
    """Developer commands used during the devlopment process of TicketFlash."""
    if PRODUCTION or not DEVMODE:
        print(
            "ERROR: To access these commands, tf cannot be running in production mode.",
            "It must be running in dev mode.",
            sep="\n",
        )
        sys.exit(1)


@dev.command
def export_schema() -> None:
    """
    Export a new schema version
    """
    _cmd_wrapper(_export_schema)


def _export_schema() -> None:
    export_path = Path(__file__).resolve().parent / "backend" / "schema"
    if not export_path.exists():
        export_path.mkdir()

    schema_export_path = export_path / str(SCHEMA_VERSION)
    # NOTE: this should be uncommented once we transition to being a stable release
    # if schema_export_path.exists():
    #     raise BaseError(f"Schema directory v{SCHEMA_VERSION} already exists")
    schema_export_path.mkdir(exist_ok=True)

    export_dict, init_statement = DEF_TABLE.export_schema()
    schema_file = schema_export_path / "schema.json"
    schema_file.write_text(json.dumps(export_dict, indent=2), encoding="utf-8")
    init_file = schema_export_path / "schema.sql"
    init_file.write_text(init_statement, encoding="utf-8")


if __name__ == "__main__":
    main()
