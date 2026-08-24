"""
API endpoints.
Need to be loaded by the server.
"""

from aiohttp import web

from . import PATH_V1, VERSION


class Endpoint:
    """
    A base class for endpoints that shows what they should look like.
    Mostly used as an interface in other parts of the code
    """

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

    def __init__(self) -> None:
        self.path = "/health"

    async def get(self, _: web.Request) -> web.Response:
        return web.json_response({"version": VERSION, "web": "ok"})

    def register(self) -> list[web.RouteDef]:
        return [web.get(self.path, self.get)]


_endpoints.append(Health)


class Users(Endpoint):
    """
    Creation of users.
    Not for authentication!
    """

    def __init__(self) -> None:
        self.path = PATH_V1 + "/users"

    async def create(self, request: web.Request) -> web.Response:
        pass

    def register(self) -> list[web.RouteDef]:
        return [web.post(self.path, self.create)]
