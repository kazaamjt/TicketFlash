"""
API endpoints.
Need to be loaded by the server.
"""

import json
from typing import TypeVar
from uuid import UUID

import asyncpg
from aiohttp import web
from pydantic import ValidationError

from ..backend.database import SCHEMA_VERSION, Database
from ..backend.objects import User, UserMetadata
from . import PATH_V1, VERSION
from .request_objects import HTTPRequestModel, UserCreateRequest

T = TypeVar("T", bound=HTTPRequestModel)


async def validate_data(
    validation_class: type[T], request: web.Request
) -> T | web.Response:
    """
    Validates data given an HTTPRequestModel Subclass.
    Then returns a validated object OR an error response.
    """
    try:
        validated_data = validation_class(**await request.json())
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
        """Returns the status off all internal systems."""
        status_all = "ok"
        db_status = await self.db.status()
        if db_status != "ok":
            status_all = "degraded"
        return web.json_response(
            {
                "status all": status_all,
                "web": {"status": "ok", "version": VERSION},
                "database": {"status": db_status, "schema version": SCHEMA_VERSION},
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
        validated_request = await validate_data(UserCreateRequest, request)
        if isinstance(validated_request, web.Response):
            return validated_request

        try:
            user, metadata = await validated_request.create_user(self.db)
        except asyncpg.exceptions.UniqueViolationError:
            return web.json_response({"error": "Email already registered"}, status=409)

        return web.json_response(
            {
                **user.model_dump(mode="json", exclude={"activated"}),
                "metadata": metadata.model_dump(
                    mode="json",
                    exclude={"user_id"},
                    exclude_none=True,
                ),
            },
            status=201,
        )

    async def get_by_email(self, request: web.Request) -> web.Response:
        """Get the user, using a email as a lookup."""
        email = request.query.get("email")
        if not email:
            raise web.HTTPBadRequest(text="Missing email parameter.")

        user = await User.get_by_email(self.db, email)
        if user is None:
            raise web.HTTPNotFound(text="User not found.")

        user_meta = await UserMetadata.get_by_id(self.db, user.id)
        if user_meta is not None:
            metadata = user_meta.model_dump(
                mode="json",
                exclude={"user_id"},
                exclude_none=True,
            )
        else:
            metadata = {}

        return web.json_response(
            {
                **user.model_dump(mode="json"),
                "metadata": metadata,
            },
        )

    async def get_by_id(self, request: web.Request) -> web.Response:
        """Gets a user by its UUID"""
        unformatted_user_id = request.match_info["user_id"]
        try:
            user_id = UUID(unformatted_user_id)
        except ValueError:
            return web.Response(body="Not a valid UUID", status=400)

        user = await User.get_by_id(self.db, user_id)
        if user is None:
            raise web.HTTPNotFound(text="User not found.")

        user_meta = await UserMetadata.get_by_id(self.db, user_id)
        if user_meta is not None:
            metadata = user_meta.model_dump(
                mode="json",
                exclude={"user_id"},
                exclude_none=True,
            )
        else:
            metadata = {}

        return web.json_response(
            {
                **user.model_dump(mode="json"),
                "metadata": metadata,
            },
        )

    def register(self) -> list[web.RouteDef]:
        return [
            web.post(self.path, self.create),
            web.get(self.path, self.get_by_email),
            web.get(self.path + "/{user_id}", self.get_by_id),
        ]


register_endpoint(Users)
