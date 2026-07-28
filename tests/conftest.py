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

import pytest
import pytest_asyncio

from backend import config
from backend.database import Database


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


@pytest_asyncio.fixture
async def tmp_database(tmp_env: os._Environ[str]) -> AsyncIterator[Database]:
    test_id = _random_string()
    tmp_env["TF_PG_HOST"] = "127.0.0.1"
    tmp_env["TF_PG_USER"] = f"test_user_{test_id}"
    tmp_env["TF_PG_PASS"] = test_id
    tmp_env["TF_PG_DB_NAME"] = f"test_{test_id}"
    old_get_pass = config.get_pass
    config.get_pass = get_pass
    old_get_input = config.get_input
    config.get_input = get_input
    database = Database()
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
    await database._connection.execute(f'DROP DATABASE "test_{test_id}"')
    await database.disconnect()
