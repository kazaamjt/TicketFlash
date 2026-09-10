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

from . import __version__, config
from .backend.database import SCHEMA_VERSION, Database
from .backend.object_def_table import DEF_TABLE
from .error import BaseError
from .server import Server
from .types import JsonSchema

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
def dev() -> None:
    """Developer commands. Should not be touched by third parties."""


@dev.command
def export_schema() -> None:
    """
    Export a new schema version
    """
    _cmd_wrapper(_export_schema)


def _export_schema() -> None:
    export_path = Path(__file__).resolve().parent.parent / "schema"
    if not export_path.exists():
        export_path.mkdir()

    schema_export_path = export_path / str(SCHEMA_VERSION)
    if schema_export_path.exists():
        raise BaseError(f"Schema directory v{SCHEMA_VERSION} already exists")
    schema_export_path.mkdir()

    export_dict: dict[str, JsonSchema] = {}
    for name, cls in DEF_TABLE.api_classes.items():
        export_dict[name] = cls.model_json_schema()

    schema_file = schema_export_path / "schema.json"
    schema_file.write_text(json.dumps(export_dict, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
