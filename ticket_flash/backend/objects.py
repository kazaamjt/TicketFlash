"""
These classes represent our objects internally and
allow for using, updating and storing said objects in the database
as well as retrieving them and representing them to the frontend.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, ClassVar
from uuid import UUID

from pydantic import BaseModel, Field

from ..types import Json, JsonSchema, assert_type
from .object_def_table import register

if TYPE_CHECKING:
    from .database import Database


class SQLStatementGenerationError(Exception):
    """An error that occures duing SQL statement generation."""


class LookupKeyError(Exception):
    """Program ran in to an unforseen programming error."""


class BackendObject(BaseModel):
    """
    Base class from which all Api objects should inherit.
    """

    table_name: ClassVar[str | None] = None
    primary_key: ClassVar[str]
    uniques: ClassVar[list[str]] = []
    foreign_keys: ClassVar[dict[str, dict[str, str]]] = {}

    @classmethod
    def export_schema(cls) -> JsonSchema:
        """creates a jsonschema of the given class. Including custom fields we added."""
        export_dict = cls.model_json_schema()
        export_dict["primary_key"] = cls.primary_key
        export_dict["table_name"] = cls.table_name
        export_dict["uniques"] = cls.uniques
        export_dict["foreign_keys"] = cls.foreign_keys

        return export_dict

    @classmethod
    def gen_create_statement(cls) -> str:
        """Generates a full SQL CREATE TABLE statement, human-readable."""
        statement = f"CREATE TABLE {cls.get_table_name()} (\n"
        export_schema = cls.export_schema()
        properties = assert_type(export_schema["properties"], dict)
        required = assert_type(export_schema["required"], list)
        for name, x in properties.items():
            statement += f"    {name} "
            prop = assert_type(x, dict)
            prop_type = _interpret_type(name, prop)
            statement += prop_type.type
            if name == cls.primary_key:
                statement += " PRIMARY KEY"
            else:
                if name in required:
                    statement += " NOT NULL"
                if name in cls.uniques:
                    statement += " UNIQUE"

            foreign_key_mapping = cls.foreign_keys.get(name)
            if foreign_key_mapping is not None:
                indent = "        "
                if len(foreign_key_mapping) != 1:
                    raise SQLStatementGenerationError(
                        "Expected exactly 1 foreign key mapping."
                    )
                for table, key in foreign_key_mapping.items():
                    statement += "\n" + indent + f"REFERENCES {table}({key})"
                    statement += "\n" + indent + "ON DELETE CASCADE"

            statement += ",\n"

        statement = statement[:-2] + "\n);"
        return statement

    @classmethod
    def get_table_name(cls) -> str:
        """Returns sql table name"""
        if cls.table_name is not None:
            return cls.table_name

        return cls.__name__.lower()

    async def insert(self, db: "Database") -> None:
        """Inserts the object in tot he database"""
        raise NotImplementedError


@dataclass
class Property:
    """JsonSchema property interpretation"""

    name: str
    type: str = ""
    nullable: bool = False


def _interpret_type(name: str, obj: dict[str, Json]) -> Property:
    prop = Property(name)
    any_of = obj.get("anyOf")
    _max_length: int | None = None
    if any_of is not None:
        any_of = assert_type(any_of, list)
        if len(any_of) < 2:
            raise SQLStatementGenerationError(
                f"Expected 2 potential types, got len({any_of})."
            )

        _type_obj = any_of[0]
        prop.nullable = True

    else:
        _type_obj = obj

    _type_obj = assert_type(_type_obj, dict)
    _type = _type_obj.get("type")
    if _type == "string":
        _format = _type_obj.get("format")
        if _format is not None:
            _type = _format

        _ml = _type_obj.get("maxLength")
        if _ml is not None:
            _max_length = assert_type(_ml, int)

    _jsonschema_type = assert_type(_type, str)
    prop.type = _jsonschema_type_to_sql_type(_jsonschema_type, _max_length)

    return prop


_jsonschema_type_to_sql_matrix = {
    "string": "VARCHAR",
    "date-time": "TIMESTAMPTZ",
    "uuid": "UUID",
    "integer": "INTEGER",
    "boolean": "BOOLEAN",
}


def _jsonschema_type_to_sql_type(_type: str, max_length: int | None) -> str:
    sql_type = _jsonschema_type_to_sql_matrix.get(_type)
    if sql_type is None:
        raise SQLStatementGenerationError(
            f"Failed to convert jsonschema type '{_type}' to SQL type."
        )

    if sql_type == "VARCHAR":
        if max_length is None:
            sql_type = "TEXT"
        else:
            sql_type = f"VARCHAR({max_length})"

    return sql_type


class User(BackendObject):
    """
    Represents a simple user.
    """

    primary_key = "id"
    table_name = "users"
    uniques = ["email"]

    id: UUID
    email: str = Field(max_length=255)

    async def insert(self, db: "Database") -> None:
        statement = f"INSERT INTO {self.get_table_name()} "
        statement += "(id, email) VALUES($1, $2)"
        await db.execute(statement, self.id, self.email)

    @classmethod
    async def get_by_id(cls, db: "Database", user_id: UUID) -> "User | None":
        """Retrieve using its id."""
        query = "id = $1"
        return await cls._get(db, query, user_id)

    @classmethod
    async def get_by_email(cls, db: "Database", email: str) -> "User | None":
        """Retrieve using its email address."""
        query = "email = $1"
        return await cls._get(db, query, email)

    @classmethod
    async def _get(cls, db: "Database", query: str, arg: object) -> "User | None":
        statement = f"SELECT * FROM {cls.get_table_name()} WHERE "
        statement += query
        row = await db.fetchrow(statement, arg)
        if row is None:
            return None

        return User(**row)


register(User)


class UserMetadata(BackendObject):
    """Additional data of the user."""

    primary_key = "user_id"
    table_name = "user_metadata"
    foreign_keys = {"user_id": {User.get_table_name(): "id"}}

    user_id: UUID
    created_at: datetime
    first_name: str | None = Field(max_length=255, default=None)
    last_name: str | None = Field(max_length=255, default=None)
    address: str | None = Field(max_length=1000, default=None)
    postal_code: int | None = None
    city: str | None = Field(max_length=255, default=None)
    telephone: str | None = Field(max_length=20, default=None)

    async def insert(self, db: "Database") -> None:
        statement = f"INSERT INTO {self.get_table_name()} "
        statement += "(user_id, created_at, first_name, last_name, address, postal_code, city, telephone) "
        statement += "VALUES($1, $2, $3, $4, $5, $6, $7, $8)"
        await db.execute(
            statement,
            self.user_id,
            self.created_at,
            self.first_name,
            self.last_name,
            self.address,
            self.postal_code,
            self.city,
            self.telephone,
        )

    @classmethod
    async def get_by_id(cls, db: "Database", user_id: UUID) -> "UserMetadata | None":
        """Retrieve using its id."""
        statement = f"SELECT * FROM {cls.get_table_name()} WHERE "
        statement += "user_id = $1"
        row = await db.fetchrow(statement, user_id)
        if row is None:
            return None

        return UserMetadata(**row)


register(UserMetadata)


class UserLogin(BackendObject):
    """Additional data of the user."""

    primary_key = "user_id"
    table_name = "user_logins"
    foreign_keys = {"user_id": {User.get_table_name(): "id"}}

    user_id: UUID
    password_hash: str
    pepper_version: int
    active: bool = False

    async def insert(self, db: "Database") -> None:
        statement = f"INSERT INTO {self.get_table_name()} "
        statement += "(user_id, password) "
        statement += "VALUES($1, $2)"
        await db.execute(statement, self.user_id, self.password_hash)


register(UserLogin)
