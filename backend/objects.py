"""
These classes represent our objects internally and
allow for using, updating and storing the, in the database
as well as retrieving them and representing them to the user.
"""

from dataclasses import dataclass

from .database import Database


@dataclass
class ApiObject:
    """
    Base class from which all Api objects should inherit.
    """

    @classmethod
    async def init(cls, db: Database) -> None:
        raise NotImplementedError


@dataclass
class User(ApiObject):

    user_id: str
    first_name: str
    last_name: str
    address: str
    postal_code: int
    telephone: str
    email: str
