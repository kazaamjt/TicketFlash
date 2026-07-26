from dataclasses import dataclass

from .database import Database


@dataclass
class ApiObject:

    @classmethod
    async def init_db_table(cls, db: Database) -> None:
        raise NotImplementedError


@dataclass
class User(ApiObject):

    first_name: str
    last_name: str
    address: str
    postal_code: int
    telephone: str
    email: str

    @classmethod
    async def init_db_table(cls, db: Database) -> None:
        raise NotImplementedError
