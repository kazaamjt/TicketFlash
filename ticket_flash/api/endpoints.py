"""
API endpoints.
Need to be loaded by the server.
"""

import json
from typing import TypeVar

from aiohttp import web
from pydantic import ValidationError

from ..backend.database import SCHEMA_VERSION, Database
from . import PATH_V1, VERSION
from .request_objects import HTTPRequestModel, UserCreateRequest

T = TypeVar("T", bound=HTTPRequestModel)


def validate_data(validation_class: type[T], data: dict) -> T | web.Response:
    """
    Validates data given an HTTPRequestModel Subclass.
    Then returns a validatedobject OR a error response.
    """
    try:
        validated_data = validation_class(**data)
    except ValidationError as e:
        return web.json_response(
            {"error": "validation_error", "details": e.errors()}, status=422
        )
    except json.JSONDecodeError:
        return web.json_response({"error": "json_decode_error"}, status=400)

    return validated_data


class Endpoint:
    """
    A base class for endpoints that shows what they should look like.
    Mostly used as an interface in other parts of the code.
    It's path class variable should be overwritten.
    """

    path = ""

    def __init__(self, db: Database) -> None:
        self.db = db

    def register(self) -> list[web.RouteDef]:
        """
        Inheriting classes should overwrite this function and
        append their endpoints to the passed list.
        """
        raise NotImplementedError


EndpointRegistry = list[type[Endpoint]]
_endpoints: EndpointRegistry = []


def register_endpoint(endpoint: type[Endpoint]) -> None:
    """Adds an endpoint to the global endpoint registry."""
    _endpoints.append(endpoint)


def get_endpoints() -> EndpointRegistry:
    return _endpoints


class Health(Endpoint):
    """
    Returns information on how various subsections of the application are doing.
    """

    path = "/health"

    async def get(self, _: web.Request) -> web.Response:
        # TODO: implement database health check
        return web.json_response(
            {
                "web": {"status": "ok", "version": VERSION},
                "database": {"status": "ok", "schema version": SCHEMA_VERSION},
            }
        )

    def register(self) -> list[web.RouteDef]:
        return [web.get(self.path, self.get)]


register_endpoint(Health)


class Users(Endpoint):
    """
    Creation of users.
    Not for authentication!
    """

    path = PATH_V1 + "/users"

    async def create(self, request: web.Request) -> web.Response:
        """
        Creates a user
        """
        validated_request = validate_data(UserCreateRequest, await request.json())
        if isinstance(validated_request, web.Response):
            return validated_request

        user, metadata = validated_request.create_user()

        return web.json_response(
            {
                **user.model_dump(mode="json"),
                "metadata": metadata.model_dump(
                    mode="json", exclude={"id"}, exclude_none=True
                ),
            },
            status=201,
        )

    def register(self) -> list[web.RouteDef]:
        return [web.post(self.path, self.create)]


register_endpoint(Users)
