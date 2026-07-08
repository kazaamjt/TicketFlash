"""
The overarching system that manages the webserver and database
and makes them play nice.
"""

import logging
from ipaddress import IPv4Address

from aiohttp import web

from . import config, is_prod

logger = logging.getLogger(__name__)


class HTTPSettings:
    """Class that loads the HTTP server settings."""

    def __init__(self) -> None:
        self.bind_ip = config.get_ip("http", "bind_ip", IPv4Address("127.0.0.1"))
        self.port = config.get_int("http", "port", 3000)

        if not 0 < self.port < 65535:
            raise config.BadOptionValue("Port should be between 0 and 65535.")


ROUTES = web.RouteTableDef()


class Server:
    """
    The overarching system that manages the webserver and database
    and makes them play nice.
    """

    def __init__(self) -> None:
        self.http_settings = HTTPSettings()

    def start(self) -> None:
        """
        Sets up and starts the server.
        """
        app = web.Application()
        app.add_routes(ROUTES)
        logger.info("Starting server.")
        if is_prod:
            web.run_app(
                app,
                host=str(self.http_settings.bind_ip),
                port=self.http_settings.port,
                print=None,
            )
        else:
            web.run_app(
                app,
                host=str(self.http_settings.bind_ip),
                port=self.http_settings.port,
            )
