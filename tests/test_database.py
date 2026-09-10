# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
# pylint: disable=unused-argument
import asyncpg
import pytest
from pytest_mock import MockerFixture

from ticket_flash.backend.database import Database


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
