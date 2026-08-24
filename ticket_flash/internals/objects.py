"""
These classes represent our objects internally and
allow for using, updating and storing said objects in the database
as well as retrieving them and representing them to the frontend.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


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

    uuid: UUID
    email: str
    created_at: datetime


class UserMetadata(BackendObject):
    """Additional data of the user."""

    uuid: UUID
    first_name: str
    last_name: str
    address: str
    postal_code: int
    telephone: str
