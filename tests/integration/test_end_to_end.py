# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-statements
# pylint: disable=unused-argument
"""
End to end tests, these migt be sloz.
Make sure the loop_scope is set to "session" for every test touching the DB layer.
"""

from datetime import datetime

import pytest
from aiohttp.test_utils import TestClient

from ticket_flash.api import VERSION, endpoints
from ticket_flash.backend.database import SCHEMA_VERSION, Database
from ticket_flash.backend.objects import User, UserMetadata


@pytest.mark.asyncio(loop_scope="session")
async def test_endpoint_health(http_client: TestClient) -> None:
    assert endpoints.Health.path == "/health"
    response = await http_client.get("/health")
    assert response.status == 200
    json_resp = await response.json()
    assert json_resp == {
        "status all": "ok",
        "web": {"status": "ok", "version": VERSION},
        "database": {"status": "ok", "schema version": SCHEMA_VERSION},
    }


@pytest.mark.asyncio(loop_scope="session")
async def test_endpoint_users_e2e(
    http_client: TestClient, random_phone_number: str, tmp_database: Database
) -> None:
    assert endpoints.Users.path == "/v1/users"

    response_1 = await http_client.post(
        endpoints.Users.path,
        json={"email": "test_endpoint_users_e2e@test.com", "password": "password"},
    )
    assert response_1.status == 201
    response_1_json = await response_1.json()
    assert isinstance(response_1_json, dict)
    assert response_1_json == {
        "id": response_1_json["id"],
        "email": "test_endpoint_users_e2e@test.com",
        "metadata": {
            "created_at": response_1_json["metadata"]["created_at"],
        },
    }

    verify_user_1 = await User.get_by_id(tmp_database, response_1_json["id"])
    assert verify_user_1 is not None
    assert verify_user_1.email == "test_endpoint_users_e2e@test.com"
    verify_user_1_meta = await UserMetadata.get_by_id(
        tmp_database, response_1_json["id"]
    )
    assert verify_user_1_meta is not None
    assert verify_user_1_meta.created_at == datetime.fromisoformat(
        response_1_json["metadata"]["created_at"]
    )

    response_taken_email = await http_client.post(
        endpoints.Users.path,
        json={"email": "test_endpoint_users_e2e@test.com", "password": "password"},
    )
    assert response_taken_email.status == 409

    response_2 = await http_client.post(
        endpoints.Users.path,
        json={
            "email": "test_endpoint_users_e2e_e2e_2@test.com",
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
        "email": "test_endpoint_users_e2e_e2e_2@test.com",
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

    verify_user_2 = await User.get_by_id(tmp_database, response_2_json["id"])
    assert verify_user_2 is not None
    assert verify_user_2.email == "test_endpoint_users_e2e_e2e_2@test.com"
    verify_user_2_meta = await UserMetadata.get_by_id(
        tmp_database, response_2_json["id"]
    )
    assert verify_user_2_meta is not None
    assert verify_user_2_meta.created_at == datetime.fromisoformat(
        response_2_json["metadata"]["created_at"]
    )
