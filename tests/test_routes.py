"""Coverage for the route skeletons in openvols.api.routers.

These routes have no data layer wired up yet, so the tests only confirm the
HTTP contract: the right shape goes in, a 200 comes back, and the response
validates against each route's response_model.
"""

import fastapi.testclient
import pytest

from openvols.api import routers


@pytest.fixture
def client():
    return fastapi.testclient.TestClient(routers.app)


# ---- Payload fixtures ------------------------------------------------------
# Each fixture returns a dict shaped like the corresponding request model.
# Fixtures that nest another model (e.g. a Role's organization/user) depend on
# the fixture for that model instead of duplicating its fields.


@pytest.fixture
def organization_body():
    return {
        "name": "Example Organization",
        "description": "A volunteer organization",
        "website": "https://example.org",
        "contact": "Jane Doe",
        "email": "contact@example.org",
        "phone": "+12025550182",
        "private_allowed": False,
        "approved": True,
    }


@pytest.fixture
def user_body():
    return {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.org",
        "email_reminders": True,
        "phone": "+12025550182",
        "phone_reminders": True,
    }


@pytest.fixture
def role_body(organization_body, user_body):
    return {"organization": organization_body, "user": user_body, "type": 0}


@pytest.fixture
def location_body(organization_body):
    return {
        "organization": organization_body,
        "name": "Community Center",
        "address": "123 Main St",
        "city": "Springfield",
        "state": "IL",
        "postal_code": "62701",
        "country": "US",
    }


@pytest.fixture
def agreement_body(organization_body):
    return {
        "organization": organization_body,
        "title": "Volunteer Waiver",
        "description": "Standard liability waiver",
        "content": "By participating you agree to the terms.",
        "valid": "2026-01-01T00:00:00Z",
        "invalid": "2027-01-01T00:00:00Z",
        "cadence": "per_opportunity",
    }


@pytest.fixture
def opportunity_body(location_body, user_body):
    return {
        "title": "Park Cleanup",
        "description": "Help clean up the park",
        "location": location_body,
        "start": "2026-06-01T09:00:00Z",
        "end": "2026-06-01T12:00:00Z",
        "public": True,
        "open": True,
        "cancelled": False,
        "completed": False,
        "contact": user_body,
        "capacity": 10,
        "notes": "",
        "auto_approve_registrants": True,
        "auto_approve_waiters": True,
    }


@pytest.fixture
def participant_body(user_body, opportunity_body):
    return {
        "user": user_body,
        "opportunity": opportunity_body,
        "approved": True,
        "cancelled": False,
        "attended": False,
    }


# ---- CRUD route coverage ----------------------------------------------------
# Every model gets the same create/list/get/update/delete routes, so the
# coverage is parametrized across resources instead of duplicated per model.

RESOURCES = [
    ("organizations", "organization_body"),
    ("users", "user_body"),
    ("roles", "role_body"),
    ("locations", "location_body"),
    ("agreements", "agreement_body"),
    ("opportunities", "opportunity_body"),
    ("participants", "participant_body"),
]


@pytest.mark.parametrize("resource, body_fixture", RESOURCES)
def test_create(client, request, resource, body_fixture):
    body = request.getfixturevalue(body_fixture)

    response = client.post(f"/api/{resource}", json={"body": body})

    assert response.status_code == 200
    assert response.json()["id"]


@pytest.mark.parametrize("resource, body_fixture", RESOURCES)
def test_list(client, resource, body_fixture):
    response = client.get(f"/api/{resource}")

    assert response.status_code == 200
    assert response.json() == {resource: []}


@pytest.mark.parametrize("resource, body_fixture", RESOURCES)
def test_get(client, resource, body_fixture):
    response = client.get(f"/api/{resource}/some-id")

    assert response.status_code == 200
    assert response.json()["id"] == "some-id"


@pytest.mark.parametrize("resource, body_fixture", RESOURCES)
def test_update(client, request, resource, body_fixture):
    body = request.getfixturevalue(body_fixture)

    response = client.patch(f"/api/{resource}/some-id", json={"body": body})

    assert response.status_code == 200
    assert response.json()["id"] == "some-id"


@pytest.mark.parametrize("resource, body_fixture", RESOURCES)
def test_delete(client, resource, body_fixture):
    response = client.delete(f"/api/{resource}/some-id")

    assert response.status_code == 200


# ---- Auth routes -------------------------------------------------------------


def test_login(client):
    response = client.post("/api/auth/login", json={"body": {"email": "jane@example.org"}})

    assert response.status_code == 200


def test_validate_token(client):
    response = client.get("/api/auth/validate", params={"token": "some-token"})

    assert response.status_code == 200
