# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
# pylint: disable=unused-argument
import pytest
from aiohttp.test_utils import TestClient

from ticket_flash.api import VERSION, endpoints
from ticket_flash.backend.database import SCHEMA_VERSION


@pytest.mark.asyncio
async def test_endpoint_health(http_client: TestClient) -> None:
    assert endpoints.Health.path == "/health"
    response = await http_client.get("/health")
    assert response.status == 200
    json_resp = await response.json()
    assert json_resp == {
        "web": {"status": "ok", "version": VERSION},
        "database": {"status": "ok", "schema version": SCHEMA_VERSION},
    }


@pytest.mark.asyncio
async def test_endpoint_users(
    http_client: TestClient, random_phone_number: str
) -> None:
    # TODO: finish implementation
    assert endpoints.Users.path == "/v1/users"
    response_1 = await http_client.post(
        endpoints.Users.path, json={"email": "test@test.com"}
    )
    assert response_1.status == 201

    response_2 = await http_client.post(
        endpoints.Users.path,
        json={
            "email": "test@test.com",
            "first_name": "test",
            "last_name": "test",
            "address": "test street",
            "postal_code": 1000,
            "city": "test",
            "telephone": random_phone_number,
        },
    )

    assert response_2.status == 201
