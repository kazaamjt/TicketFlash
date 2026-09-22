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
async def test_endpoint_health(http_client_mock_db: TestClient) -> None:
    assert endpoints.Health.path == "/health"
    response = await http_client_mock_db.get("/health")
    assert response.status == 200
    json_resp = await response.json()
    assert json_resp == {
        "status all": "ok",
        "web": {"status": "ok", "version": VERSION},
        "database": {"status": "ok", "schema version": SCHEMA_VERSION},
    }


@pytest.mark.asyncio
async def test_endpoint_users(
    http_client_mock_db: TestClient, random_phone_number: str
) -> None:
    assert endpoints.Users.path == "/v1/users"

    response_1 = await http_client_mock_db.post(
        endpoints.Users.path,
        json={"email": "test_endpoint_users@test.com", "password": "password"},
    )
    assert response_1.status == 201
    response_1_json = await response_1.json()
    assert isinstance(response_1_json, dict)
    assert response_1_json == {
        "id": response_1_json["id"],
        "email": "test_endpoint_users@test.com",
        "metadata": {
            "created_at": response_1_json["metadata"]["created_at"],
        },
    }

    response_2 = await http_client_mock_db.post(
        endpoints.Users.path,
        json={
            "email": "test2@test.com",
            "password": "password",
            "first_name": "test",
            "last_name": "test",
            "address": "test street",
            "postal_code": 1000,
            "city": "test",
            "telephone": random_phone_number,
        },
    )

    assert response_2.status == 201
    response_2_json = await response_2.json()
    assert isinstance(response_2_json, dict)
    assert response_2_json == {
        "id": response_2_json["id"],
        "email": "test2@test.com",
        "metadata": {
            "first_name": "test",
            "last_name": "test",
            "created_at": response_2_json["metadata"]["created_at"],
            "address": "test street",
            "postal_code": 1000,
            "city": "test",
            "telephone": random_phone_number,
        },
    }
