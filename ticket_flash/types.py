"""
Custom type definitions.
"""

from datetime import datetime, timezone
from typing import Any, TypeAlias, TypeVar

Json: TypeAlias = None | bool | int | float | str | list["Json"] | dict[str, "Json"]

JsonSchema: TypeAlias = dict[str, Json]


def now() -> datetime:
    """Gets the current time and rertuns it as timezone aware timestamp."""
    return datetime.now(timezone.utc)


T = TypeVar("T")


def assert_type(obj: Any, required_type: type[T]) -> T:
    """
    runtime check to make sure we got the type we're expecting to get.
    """
    if not isinstance(obj, required_type):
        raise TypeError(
            f"During statement generation, expected type '{required_type.__name__}'"
            f"but got '{type(obj)}'"
        )

    return obj
