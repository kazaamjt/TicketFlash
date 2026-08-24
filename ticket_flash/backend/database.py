"""
Interface for talking to the postgres db.
"""

import logging

import asyncpg
from asyncpg import Connection, Record
from pydantic import BaseModel

from .. import config
from ..error import BaseError

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1


class Schema(BaseModel):
    version: int


class DBError(BaseError):
    """ "Something went wrong during a db operation."""


class DatabaseSettings:
    """Postgress settings"""

    def __init__(self) -> None:
        section = "pg"
        logger.debug("Getting config from env.")
        self.host = config.get(section, "host")
        self.port = config.get_int(section, "port", 5432)
        self.user = config.get(section, "user")
        self.password = config.get(section, "pass")
        self.db_name = config.get(section, "db_name")


class Database:
    """
    High level representation of the PG database.
    """

    def __init__(self) -> None:
        self.settings = DatabaseSettings()
        self._connection: Connection[Record]
        self._connected = False

    async def connect(self) -> None:
        """Connect to PG."""
        if not self._connected:
            try:
                logger.debug("Connectiong to database.")
                self._connection = await asyncpg.connect(
                    host=self.settings.host,
                    user=self.settings.user,
                    password=self.settings.password,
                    database=self.settings.db_name,
                )
            except asyncpg.exceptions.InvalidCatalogNameError as e:
                raise DBError(
                    "Database not initialized! Please run database init"
                ) from e
            except asyncpg.InvalidPasswordError as e:
                raise DBError("Failed to connect to postgres: wrong password") from e
            except asyncpg.InvalidAuthorizationSpecificationError as e:
                raise DBError(
                    "Failed to connect to postgres: wrong username or authorization"
                ) from e
            except ConnectionRefusedError as e:
                raise DBError(
                    "Failed to connect to postgres: Connection refused"
                ) from e
            except OSError as e:
                raise DBError(
                    f"Failed to connect to postgres: Host unreachable ('{self.settings.host}', {self.settings.port})"
                ) from e

            self._connected = True
            logger.info("Connected to database.")

    async def _get_schema(self) -> Schema:
        return Schema(
            version=await self._connection.fetchval(
                "SELECT version FROM schema_version"
            )
        )

    async def _verify_schema(self) -> None:
        schema = await self._get_schema()
        if not SCHEMA_VERSION == schema.version:
            raise DBError(
                f"Schema version mismatch! (Expected {SCHEMA_VERSION}, but got {schema.version})"
            )

    async def disconnect(self) -> None:
        """Closes the connection, only if it was previously connected."""
        if self._connected:
            logger.debug("Disconnecting from database.")
            await self._connection.close()
            self._connected = False
            logger.debug("Disconnected from database.")

    async def init(self, username: str | None, database: str | None) -> None:
        """
        Initializes the database for use.
        """
        if self.settings.host == "":
            self.settings.host = config.get_input("Postgres host", "localhost")

        print(
            "Starting database initialization.",
            f"(host: {self.settings.host}:{self.settings.port})",
        )
        prev_username = self.settings.user
        password = self.settings.password
        prev_database = self.settings.db_name
        self.settings.user = config.get_input("Postgres superuser", "postgres")
        self.settings.password = config.get_pass()
        self.settings.db_name = config.get_input("Default database", "postgres")
        await self.connect()
        try:
            if username is None:
                username = prev_username
                if username == "":
                    username = config.get_input(
                        "Application postgres username", "ticket_flash"
                    )
            logger.info(f"Creating new postgres user '{username}'.")
            if password == "":
                password = config.get_pass()

            await self._connection.execute(
                f"CREATE ROLE \"{username}\" LOGIN PASSWORD '{password}'"
            )

            if database is None:
                database = prev_database
                if database == "":
                    database = config.get_input(
                        "Application postgres database name", "TicketFlash"
                    )
            logger.info(f"Creating new postgres database '{database}'.")
            await self._connection.execute(
                f'CREATE DATABASE "{database}" OWNER "{username}"'
            )

        finally:
            await self.disconnect()

        print("Populating new database.")
        self.settings.user = username
        self.settings.password = password
        self.settings.db_name = database

        await self.connect()
        logger.debug(f"Schema version: {SCHEMA_VERSION}")
        await self._connection.execute("""
            CREATE TABLE schema_version (
                version INTEGER NOT NULL
            );
            """)

        await self._connection.execute(f"""
            INSERT INTO schema_version (version)
            VALUES ({SCHEMA_VERSION});
            """)

        await self.disconnect()
