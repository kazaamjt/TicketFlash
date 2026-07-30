"""
These classes represent our objects internally and
allow for using, updating and storing the, in the database
as well as retrieving them and representing them to the user.
"""

from datetime import datetime

from pydantic import BaseModel

from .object_def_table import register


class ApiObject(BaseModel):
    """
    Base class from which all Api objects should inherit.
    """

    @classmethod
    def export_schema(cls) -> None:
        pass


@register
class User(ApiObject):
    """
    Represents a simple user.
    """

    uuid: str
    email: str


@register
class UserMetadata(ApiObject):
    """Aditional data of the user."""

    uuid: str
    created_at: datetime
    first_name: str
    last_name: str
    address: str
    postal_code: int
    telephone: str
