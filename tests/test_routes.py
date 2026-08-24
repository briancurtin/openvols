"""Coverage for the routes in openvols.api.routers, backed by a real (in-memory) Store.

The client fixture runs the app's lifespan so each test gets a fresh, empty
MemoryStore -- state never leaks between tests.
"""

import fastapi.testclient
import pytest

from openvols.api import routers


@pytest.fixture
def client():
    with fastapi.testclient.TestClient(routers.app) as client:
        yield client


# ---- Payload fixtures ------------------------------------------------------
# Each *_body fixture returns a dict shaped like the corresponding request
# model. Models reference other aggregates by id (see models.py), so fixtures
# that need one (e.g. a Role's organization_id/user_id) create the referenced
# resource through the API first via an *_id fixture.


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
def organization_id(client, organization_body):
    return client.post("/api/organizations", json={"body": organization_body}).json()["id"]


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
def user_id(client, user_body):
    return client.post("/api/users", json={"body": user_body}).json()["id"]


@pytest.fixture
def role_body(organization_id, user_id):
    return {"organization_id": organization_id, "user_id": user_id, "type": 0}


@pytest.fixture
def location_body(organization_id):
    return {
        "organization_id": organization_id,
        "name": "Community Center",
        "address": "123 Main St",
        "city": "Springfield",
        "state": "IL",
        "postal_code": "62701",
        "country": "US",
    }


@pytest.fixture
def location_id(client, location_body):
    return client.post("/api/locations", json={"body": location_body}).json()["id"]


@pytest.fixture
def agreement_body(organization_id):
    return {
        "organization_id": organization_id,
        "title": "Volunteer Waiver",
        "description": "Standard liability waiver",
        "content": "By participating you agree to the terms.",
        "valid": "2026-01-01T00:00:00Z",
        "invalid": "2027-01-01T00:00:00Z",
        "cadence": "per_opportunity",
    }


@pytest.fixture
def opportunity_body(location_id, user_id):
    return {
        "title": "Park Cleanup",
        "description": "Help clean up the park",
        "location_id": location_id,
        "start": "2026-06-01T09:00:00Z",
        "end": "2026-06-01T12:00:00Z",
        "public": True,
        "open": True,
        "cancelled": False,
        "completed": False,
        "contact_id": user_id,
        "capacity": 10,
        "notes": "",
        "auto_approve_registrants": True,
        "auto_approve_waiters": True,
    }


# ---- CRUD route coverage ----------------------------------------------------
# Organizations/users/roles/locations/agreements/opportunities all share the
# same create/list/get/update/delete shape, so the coverage is parametrized
# instead of duplicated per model. Participants are covered separately below
# since registration -- not a plain create -- is how they come into being.

RESOURCES = [
    ("organizations", "organization_body"),
    ("users", "user_body"),
    ("roles", "role_body"),
    ("locations", "location_body"),
    ("agreements", "agreement_body"),
    ("opportunities", "opportunity_body"),
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
def test_get(client, request, resource, body_fixture):
    body = request.getfixturevalue(body_fixture)
    created = client.post(f"/api/{resource}", json={"body": body}).json()

    response = client.get(f"/api/{resource}/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


@pytest.mark.parametrize("resource, body_fixture", RESOURCES)
def test_get_not_found(client, resource, body_fixture):
    response = client.get(f"/api/{resource}/00000")

    assert response.status_code == 404


@pytest.mark.parametrize("resource, body_fixture", RESOURCES)
def test_update(client, request, resource, body_fixture):
    body = request.getfixturevalue(body_fixture)
    created = client.post(f"/api/{resource}", json={"body": body}).json()

    response = client.patch(f"/api/{resource}/{created['id']}", json={"body": body})

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


@pytest.mark.parametrize("resource, body_fixture", RESOURCES)
def test_delete(client, request, resource, body_fixture):
    body = request.getfixturevalue(body_fixture)
    created = client.post(f"/api/{resource}", json={"body": body}).json()

    response = client.delete(f"/api/{resource}/{created['id']}")

    assert response.status_code == 200
    assert client.get(f"/api/{resource}/{created['id']}").status_code == 404


# ---- Participants / registration engine -------------------------------------


@pytest.fixture
def registered_participant(client, user_body, opportunity_body):
    """Create a user and an opportunity, then register the user for it."""
    user = client.post("/api/users", json={"body": user_body}).json()
    opportunity = client.post("/api/opportunities", json={"body": opportunity_body}).json()

    response = client.post(
        "/api/participants",
        json={"body": {"user_id": user["id"], "opportunity_id": opportunity["id"]}},
    )
    return response.json()


def test_register_participant(registered_participant):
    assert registered_participant["id"]
    assert registered_participant["approved"] is True  # opportunity_body has capacity=10
    assert registered_participant["cancelled"] is False


def test_get_participant(client, registered_participant):
    response = client.get(f"/api/participants/{registered_participant['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == registered_participant["id"]


def test_list_participants(client, registered_participant):
    response = client.get("/api/participants")

    assert response.status_code == 200
    assert [p["id"] for p in response.json()["participants"]] == [registered_participant["id"]]


def test_update_participant(client, registered_participant):
    body = {**registered_participant, "attended": True}

    response = client.patch(
        f"/api/participants/{registered_participant['id']}", json={"body": body}
    )

    assert response.status_code == 200
    assert response.json()["attended"] is True


def test_cancel_participant(client, registered_participant):
    response = client.post(f"/api/participants/{registered_participant['id']}/cancel")

    assert response.status_code == 200
    assert response.json()["cancelled"] is True


def test_delete_participant(client, registered_participant):
    response = client.delete(f"/api/participants/{registered_participant['id']}")

    assert response.status_code == 200
    assert client.get(f"/api/participants/{registered_participant['id']}").status_code == 404


def test_registration_waitlists_over_capacity(client, user_body, opportunity_body):
    opportunity_body = {**opportunity_body, "capacity": 1}
    opportunity = client.post("/api/opportunities", json={"body": opportunity_body}).json()

    first_user = client.post("/api/users", json={"body": user_body}).json()
    second_user = client.post(
        "/api/users", json={"body": {**user_body, "email": "second@example.org"}}
    ).json()

    first = client.post(
        "/api/participants",
        json={"body": {"user_id": first_user["id"], "opportunity_id": opportunity["id"]}},
    ).json()
    second = client.post(
        "/api/participants",
        json={"body": {"user_id": second_user["id"], "opportunity_id": opportunity["id"]}},
    ).json()

    assert first["approved"] is True
    assert second["approved"] is False  # waitlisted, capacity is 1

    client.post(f"/api/participants/{first['id']}/cancel")

    promoted = client.get(f"/api/participants/{second['id']}").json()
    assert promoted["approved"] is True


# ---- Auth routes -------------------------------------------------------------


def test_login(client):
    response = client.post("/api/auth/login", json={"body": {"email": "jane@example.org"}})

    assert response.status_code == 200


def test_validate_token(client):
    response = client.get("/api/auth/validate", params={"token": "some-token"})

    assert response.status_code == 200
