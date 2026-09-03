"""
A catalog that keeps track of all the the different objects.
"""

import logging
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .objects import BackendObject

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="BackendObject")


class ObjectDefTable:
    """
    A catalog that keeps track of all the the different objects.
    Register classes to add them to the def table.
    """

    def __init__(self) -> None:
        self.api_classes: dict[str, "type[BackendObject]"] = {}

    def register(self, cls: type["BackendObject"]) -> None:
        """
        Register a subclass of ApiObject to the system.
        """
        if cls.__name__ in DEF_TABLE.api_classes:
            logger.warning(
                f"Overwriting class {cls.__name__}, a class with this name was already registered."
            )

        DEF_TABLE.api_classes[cls.__name__] = cls


DEF_TABLE = ObjectDefTable()


def register(cls: type[T]) -> type[T]:
    """
    Decorate a subclass of "ApiObject" to register it in the system.
    """
    DEF_TABLE.register(cls)
    return cls
