"""
Custom type definitions.
"""

from datetime import datetime, timezone
from typing import TypeAlias

Json: TypeAlias = None | bool | int | float | str | list["Json"] | dict[str, "Json"]

JsonSchema: TypeAlias = dict[str, Json]


def now() -> datetime:
    """Gets the current time and rertuns it as timezone aware timestamp."""
    return datetime.now(timezone.utc)
