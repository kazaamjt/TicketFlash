# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-locals
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
async def test_endpoint_users_post(
    http_client_mock_db: TestClient, random_phone_number: str, mock_pepper: None
) -> None:
    assert endpoints.Users.path == "/v1/users"

    # Minimal user create
    response_1 = await http_client_mock_db.post(
        endpoints.Users.path,
        json={
            "email": "test_endpoint_users@test.com",
            "password": "very_long_password",
        },
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

    # Full user create
    response_2 = await http_client_mock_db.post(
        endpoints.Users.path,
        json={
            "email": "test2@test.com",
            "password": "very_long_password",
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


@pytest.mark.asyncio
async def test_endpoint_users_post_failure(
    http_client_mock_db: TestClient, random_phone_number: str, mock_pepper: None
) -> None:
    # Failure 1: bad json
    response_1 = await http_client_mock_db.post(endpoints.Users.path, data="{")
    assert response_1.status == 400

    # Failure 2: missing password
    response_2 = await http_client_mock_db.post(
        endpoints.Users.path,
        json={"email": "test_endpoint_users@test.com"},
    )
    assert response_2.status == 422
    assert await response_2.json() == {
        "details": [
            {
                "loc": ["password"],
                "msg": "Field required",
                "type": "missing",
            }
        ],
        "error": "validation_error",
    }

    # Failure 3: missing email
    response_3 = await http_client_mock_db.post(
        endpoints.Users.path,
        json={"password": "very_long_password"},
    )
    assert response_3.status == 422
    assert await response_3.json() == {
        "details": [
            {
                "loc": ["email"],
                "msg": "Field required",
                "type": "missing",
            }
        ],
        "error": "validation_error",
    }

    # Failure 4: Password too short
    response_4 = await http_client_mock_db.post(
        endpoints.Users.path,
        json={
            "email": "test_endpoint_users@test.com",
            "password": "password",
        },
    )
    assert response_4.status == 422
    assert await response_4.json() == {
        "details": [
            {
                "loc": ["password"],
                "msg": "String should have at least 15 characters",
                "type": "string_too_short",
            }
        ],
        "error": "validation_error",
    }
