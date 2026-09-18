# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
# pylint: disable=unused-argument
"""
When testing the database layer,
make sure the loop_scope is set to "session"
"""

from uuid import uuid4

import asyncpg
import pytest
from pytest_mock import MockerFixture

from ticket_flash.backend.database import Database
from ticket_flash.backend.objects import User, UserMetadata
from ticket_flash.types import now


@pytest.mark.asyncio(loop_scope="session")
async def test_init(tmp_database: Database) -> None:
    """
    This function tests the init script and the tmp_database fixture.
    If it fails, most likely the other tests will also fail.
    """
    assert await tmp_database.status() == "ok"


@pytest.mark.asyncio
async def test_health_check_returns_false_on_timeout(
    tmp_database: Database, mocker: MockerFixture
) -> None:
    async def slow_query(*args: object) -> None:
        raise TimeoutError

    mocker.patch.object(tmp_database, "fetchval", side_effect=slow_query)

    assert await tmp_database._health_check(1) is False


@pytest.mark.asyncio
async def test_database_status_ok(
    tmp_database: Database, mocker: MockerFixture
) -> None:
    health_check = mocker.patch.object(
        tmp_database,
        "_health_check",
        return_value=True,
    )

    assert await tmp_database.status() == "ok"

    health_check.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_performance_degradation(
    tmp_database: Database, mocker: MockerFixture
) -> None:
    health_check = mocker.patch.object(
        tmp_database,
        "_health_check",
        side_effect=[False, True],
    )

    assert await tmp_database.status() == "performance degraded"

    assert health_check.call_args_list == [
        mocker.call(1),
        mocker.call(5),
    ]


@pytest.mark.asyncio
async def test_health_check_failure(
    tmp_database: Database, mocker: MockerFixture
) -> None:
    health_check = mocker.patch.object(
        tmp_database,
        "_health_check",
        side_effect=asyncpg.PostgresError("database error"),
    )

    assert await tmp_database.status() == "error"

    health_check.assert_called_once_with(1)


@pytest.mark.asyncio(loop_scope="session")
async def test_user_object(tmp_database: Database) -> None:
    user_id = uuid4()
    email = "test_user_object@test.local"
    user = User(id=user_id, email=email)
    await user.insert(tmp_database)

    verify_id = await User.get_by_id(tmp_database, user_id)
    assert verify_id is not None
    assert verify_id.id == user.id
    assert verify_id.email == user.email
    assert verify_id is not user

    verify_email = await User.get_by_email(tmp_database, email)
    assert verify_email is not None
    assert verify_email.id == user.id
    assert verify_email.email == user.email
    assert verify_email is not user


@pytest.mark.asyncio(loop_scope="session")
async def test_usermetadata_object(tmp_database: Database) -> None:
    user_id = uuid4()
    creation_date = now()
    user = User(id=user_id, email="test_usermetadata_object@test.local")
    await user.insert(tmp_database)
    user_metadata = UserMetadata(user_id=user_id, created_at=creation_date)
    await user_metadata.insert(tmp_database)

    verify_id = await UserMetadata.get_by_id(tmp_database, user_id)
    assert verify_id is not None
    assert verify_id.user_id == user_metadata.user_id
    assert verify_id.created_at == user_metadata.created_at
    assert verify_id is not user_metadata
