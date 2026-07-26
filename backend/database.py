"""
Interface for talking to the postgres db.
"""

import logging

import asyncpg
from asyncpg import Connection, Record

from . import config

logger = logging.getLogger(__name__)


class DatabaseSettings:
    """Postgress settings"""

    def __init__(self) -> None:
        section = "pg"
        logger.debug("Getting config from env.")
        self._host = config.get(section, "host")
        self._user = config.get(section, "user")
        self._pass = config.get(section, "pass")
        self._db = config.get(section, "db")
        self.url = f"postgresql://{self._user}:{self._pass}@{self._host}/{self._db}"


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
        self._connection = await asyncpg.connect(self.settings.url)
        self._connected = True

    async def disconnect(self) -> None:
        """Closes the connection, only if it was previously connected."""
        if self._connected:
            await self._connection.close()
            self._connected = False
