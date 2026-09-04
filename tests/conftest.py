# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
"""
Pytest fixtures live in thise file
"""

import os
import random
from copy import deepcopy
from typing import AsyncIterator, Iterable
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from aiohttp.test_utils import TestClient, TestServer

from ticket_flash import config
from ticket_flash.backend.database import Database
from ticket_flash.server import Server


@pytest.fixture
def tmp_env() -> Iterable[os._Environ[str]]:
    """
    Creates a temporary copy of os.environ
    and cleans it up after use.
    """
    env = deepcopy(os.environ)
    yield os.environ
    os.environ = env


@pytest.fixture
def random_string() -> str:
    return _random_string()


def _random_string() -> str:
    return "".join(random.choice("0123456789ABCDEF") for _ in range(20))


def get_pass(attempt: int = 0) -> str:
    return config.get("pg", "admin_pass")


def get_input(prompt: str, default: str) -> str:
    return default


@pytest_asyncio.fixture(scope="session")
async def tmp_database() -> AsyncIterator[Database]:
    """
    When using this fixture, be sure to use add (loop_scope="session")
    to whatever test uses it, because it will otherwise use a new, seperate loop.
    """
    test_id = _random_string()
    old_get_pass = config.get_pass
    config.get_pass = get_pass
    old_get_input = config.get_input
    config.get_input = get_input
    database = Database()
    database.settings.host = "127.0.0.1"
    database.settings.user = f"test_user_{test_id}"
    database.settings.password = test_id
    database.settings.db_name = f"test_{test_id}"
    await database.init(None, None)
    config.get_pass = old_get_pass
    config.get_input = old_get_input
    await database.connect()
    yield database
    await database.disconnect()
    config.get_pass = get_pass
    database.settings.user = "postgres"
    database.settings.password = config.get_pass()
    database.settings.db_name = "postgres"
    config.get_pass = old_get_pass
    await database.connect()
    await database.execute(f'DROP DATABASE "test_{test_id}"')
    await database.execute(f'DROP USER "test_user_{test_id}"')
    await database.disconnect()


@pytest.fixture
def mock_db() -> Database:
    async def status() -> str:
        return "ok"

    db = Mock(spec=Database)
    db.connect = AsyncMock()
    db.disconnect = AsyncMock()
    db.status = status
    return db


@pytest_asyncio.fixture
async def http_client(mock_db: Database) -> AsyncIterator[TestClient]:
    server = Server(mock_db)
    app = server._create_app()
    async with TestClient(TestServer(app)) as client:
        yield client


@pytest.fixture
def random_phone_number() -> str:
    return f"+1212555{random.randint(100, 199)}"
