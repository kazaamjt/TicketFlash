"""
Custom type definitions.
"""

from typing import TypeAlias

Json: TypeAlias = None | bool | int | float | str | list["Json"] | dict[str, "Json"]

JsonSchema: TypeAlias = dict[str, Json]
