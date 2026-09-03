"""
These classes represent our objects internally and
allow for using, updating and storing said objects in the database
as well as retrieving them and representing them to the frontend.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .object_def_table import register


class BackendObject(BaseModel):
    """
    Base class from which all Api objects should inherit.
    """

    @classmethod
    def export_schema(cls) -> None:
        pass


class User(BackendObject):
    """
    Represents a simple user.
    """

    id: UUID
    email: str
    created_at: datetime


register(User)


class UserMetadata(BackendObject):
    """Additional data of the user."""

    id: UUID
    first_name: str | None
    last_name: str | None
    address: str | None
    postal_code: int | None
    city: str | None
    telephone: str | None


register(UserMetadata)
