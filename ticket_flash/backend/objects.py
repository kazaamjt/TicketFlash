"""
These classes represent our objects internally and
allow for using, updating and storing said objects in the database
as well as retrieving them and representing them to the frontend.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

from ..types import Json, JsonSchema
from .object_def_table import register


class SQLStatementGenerationError(Exception):
    """An error that occures duing SQL statement generation."""


T = TypeVar("T")


def _assert_type(obj: Any, required_type: type[T]) -> T:
    """
    runtime check to make sure we got the type we're expecting to get.
    """
    if not isinstance(obj, required_type):
        raise SQLStatementGenerationError(
            f"During statement generation, expected type '{required_type.__name__}'"
            f"but got '{type(obj)}'"
        )

    return obj


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
        any_of = _assert_type(any_of, list)
        if len(any_of) < 2:
            raise SQLStatementGenerationError(
                f"Expected 2 potential types, got len({any_of})."
            )

        _type_obj = any_of[0]
        prop.nullable = True

    else:
        _type_obj = obj

    _type_obj = _assert_type(_type_obj, dict)
    _type = _type_obj.get("type")
    if _type == "string":
        _format = obj.get("format")
        if _format is not None:
            _type = _format

        _ml = obj.get("_max_length")
        if _ml is not None:
            _max_length = _assert_type(_ml, int)

    _jsonschema_type = _assert_type(_type, str)
    prop.type = _jsonschema_type_to_sql_type(_jsonschema_type, _max_length)

    return prop


_jsonschema_type_to_sql_matrix = {
    "string": "VARCHAR",
    "date-time": "TIMESTAMPTZ",
    "uuid": "UUID",
    "integer": "INTEGER",
}


def _jsonschema_type_to_sql_type(_type: str, max_length: int | None) -> str:
    sql_type = _jsonschema_type_to_sql_matrix.get(_type)
    if sql_type is None:
        raise SQLStatementGenerationError(
            "Failed to convert jsonschema type to SQL type."
        )

    if sql_type == "VARCHAR":
        if max_length is None:
            sql_type = "TEXT"
        else:
            sql_type = f"VARCHAR({max_length})"

    return sql_type


class BackendObject(BaseModel):
    """
    Base class from which all Api objects should inherit.
    """

    table_name: ClassVar[str | None] = None
    primary_key: ClassVar[str]
    uniques: ClassVar[list[str]] = []

    @classmethod
    def export_schema(cls) -> JsonSchema:
        """creates a jsonschema of the given class. Including primary key."""
        export_dict = cls.model_json_schema()
        export_dict["primary_key"] = cls.primary_key

        return export_dict

    @classmethod
    def gen_create_statement(cls) -> str:
        """Generates a full SQL CREATE TABLE statement, human-readable."""
        statement = f"CREATE TABLE {cls.get_table_name()} (\n"
        export_schema = cls.export_schema()
        properties = _assert_type(export_schema["properties"], dict)
        required = _assert_type(export_schema["required"], list)
        for name, x in properties.items():
            statement += f"    {name} "
            prop = _assert_type(x, dict)
            prop_type = _interpret_type(name, prop)
            statement += prop_type.type
            if name == cls.primary_key:
                statement += " PRIMARY KEY"
            else:
                if name in required:
                    statement += " NOT NULL"
                if name in cls.uniques:
                    statement += " UNIQUE"

            statement += ",\n"

        statement = statement[:-2] + "\n);"
        return statement

    @classmethod
    def get_table_name(cls) -> str:
        """Returns sql table name"""
        if cls.table_name is not None:
            return cls.table_name

        return cls.__name__.lower()


class User(BackendObject):
    """
    Represents a simple user.
    """

    primary_key = "id"
    table_name = "users"

    id: UUID
    email: str = Field(max_length=255)
    created_at: datetime


register(User)


class UserMetadata(BackendObject):
    """Additional data of the user."""

    primary_key = "id"
    table_name = "user-metadata"

    id: UUID
    first_name: str | None = Field(max_length=255, default=None)
    last_name: str | None = Field(max_length=255, default=None)
    address: str | None = Field(max_length=1000, default=None)
    postal_code: int | None = None
    city: str | None = Field(max_length=255, default=None)
    telephone: str | None = Field(max_length=20, default=None)


register(UserMetadata)
