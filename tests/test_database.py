# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
# pylint: disable=unused-argument
import pytest

from backend.database import Database


@pytest.mark.asyncio
async def test_init(tmp_database: Database) -> None:
    """
    This function is empty on purpose.
    It mostly tests the init script and the tmp_database fixture.
    If it fails, most likely the other tests will also fail.
    """
