"""Coverage for the routes in openvols.api.routers, backed by a real (in-memory) Store.

The client fixture runs the app's lifespan so each test gets a fresh, empty
MemoryStore -- state never leaks between tests.
"""

import fastapi.testclient
import pytest

from openvols.api import auth, routers

_LOGIN_USER_BODY = {
    "first_name": "Login",
    "last_name": "User",
    "email": "login@example.org",
    "email_reminders": True,
    "phone": "+12025550182",
    "phone_reminders": True,
}


@pytest.fixture
def client():
    """An authenticated client: every protected route needs a session to test past it."""
    # https base_url: the default Secure cookie policy means httpx's cookie
    # jar won't echo the cookie back on a later request over plain http.
    with fastapi.testclient.TestClient(routers.app, base_url="https://testserver") as client:
        client.post("/api/users", json=_LOGIN_USER_BODY)
        client.get("/api/auth/validate", params={"token": _LOGIN_USER_BODY["email"]})
        yield client


@pytest.fixture
def anonymous_client():
    with fastapi.testclient.TestClient(routers.app, base_url="https://testserver") as client:
        yield client


@pytest.fixture(params=[routers.dependencies.get_store, routers.dependencies.get_email_sender])
def anonymous_client_dependency_down(request):
    with fastapi.testclient.TestClient(routers.app, base_url="https://testserver") as client:

        class NestedHealth:
            async def get(self):
                return not bool(request.param == routers.dependencies.get_store)

        class Deps:
            health = NestedHealth()

            async def check(self):
                return not bool(request.param == routers.dependencies.get_email_sender)

        client.app.dependency_overrides[request.param] = lambda: Deps()
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
        "contact": "jane@example.org",
        "email": "contact@example.org",
        "phone": "+12025550182",
        "private_allowed": False,
        "approved": True,
    }


@pytest.fixture
def organization_id(client, organization_body):
    return client.post("/api/organizations", json=organization_body).json()["id"]


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
    return client.post("/api/users", json=user_body).json()["id"]


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
    return client.post("/api/locations", json=location_body).json()["id"]


@pytest.fixture
def agreement_body(organization_id):
    return {
        "organization_id": organization_id,
        "title": "Volunteer Waiver",
        "description": "Standard liability waiver",
        "content": "By participating in this opportunity you agree to the terms outlined here.",
        "valid": "2026-01-01T00:00:00Z",
        "invalid": "2027-01-01T00:00:00Z",
        "cadence": "per_opportunity",
    }


@pytest.fixture
def opportunity_body(location_id, user_id):
    return {
        "title": "Park Cleanup",
        "description": (
            "Join volunteers for a community cleanup at the park: picking up litter, "
            "weeding garden beds, repainting benches, and clearing walking trails."
        ),
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

    response = client.post(f"/api/{resource}", json=body)

    assert response.status_code == 200
    assert response.json()["id"]


@pytest.mark.parametrize("resource, body_fixture", RESOURCES)
def test_list(client, resource, body_fixture):
    response = client.get(f"/api/{resource}")

    assert response.status_code == 200
    if resource == "users":
        # The client fixture's login user is already in the store.
        assert [u["email"] for u in response.json()["users"]] == [_LOGIN_USER_BODY["email"]]
    else:
        assert response.json() == {resource: []}


@pytest.mark.parametrize("resource, body_fixture", RESOURCES)
def test_get(client, request, resource, body_fixture):
    body = request.getfixturevalue(body_fixture)
    created = client.post(f"/api/{resource}", json=body).json()

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
    created = client.post(f"/api/{resource}", json=body).json()

    response = client.patch(f"/api/{resource}/{created['id']}", json=body)

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


# ---- Participants / registration engine -------------------------------------


@pytest.fixture
def registered_participant(client, user_body, opportunity_body):
    """Create a user and an opportunity, then register the user for it."""
    user = client.post("/api/users", json=user_body).json()
    opportunity = client.post("/api/opportunities", json=opportunity_body).json()

    response = client.post(
        "/api/participants",
        json={"user_id": user["id"], "opportunity_id": opportunity["id"]},
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

    response = client.patch(f"/api/participants/{registered_participant['id']}", json=body)

    assert response.status_code == 200
    assert response.json()["attended"] is True


def test_cancel_participant(client, registered_participant):
    response = client.post(f"/api/participants/{registered_participant['id']}/cancel")

    assert response.status_code == 200
    assert response.json()["cancelled"] is True
    assert response.json()["approved"] is False


def test_registration_waitlists_over_capacity(client, user_body, opportunity_body):
    opportunity_body = {**opportunity_body, "capacity": 1}
    opportunity = client.post("/api/opportunities", json=opportunity_body).json()

    first_user = client.post("/api/users", json=user_body).json()
    second_user = client.post(
        "/api/users", json={**user_body, "email": "second@example.org"}
    ).json()

    first = client.post(
        "/api/participants",
        json={"user_id": first_user["id"], "opportunity_id": opportunity["id"]},
    ).json()
    second = client.post(
        "/api/participants",
        json={"user_id": second_user["id"], "opportunity_id": opportunity["id"]},
    ).json()

    assert first["approved"] is True
    assert second["approved"] is False  # waitlisted, capacity is 1

    client.post(f"/api/participants/{first['id']}/cancel")

    promoted = client.get(f"/api/participants/{second['id']}").json()
    assert promoted["approved"] is True


# ---- Auth routes -------------------------------------------------------------


def test_login(client):
    response = client.post("/api/auth/login", json={"email": "jane@example.org"})

    assert response.status_code == 200


# /api/auth/validate's cookie-issuing behavior is covered in tests/unit/test_auth.py.


# ---- Session enforcement (#72) -----------------------------------------------
# Every route the TDD marks authenticated must 401 without a session. Bodies
# don't matter here -- require_session runs before the handler ever sees one --
# so a placeholder id is enough for the path-parameter routes.

PROTECTED_ROUTES = [
    ("POST", "/api/organizations"),
    ("PATCH", "/api/organizations/1"),
    ("GET", "/api/users"),
    ("GET", "/api/users/1"),
    ("PATCH", "/api/users/1"),
    ("DELETE", "/api/users/1"),
    ("POST", "/api/roles"),
    ("GET", "/api/roles"),
    ("GET", "/api/roles/1"),
    ("PATCH", "/api/roles/1"),
    ("POST", "/api/locations"),
    ("PATCH", "/api/locations/1"),
    ("POST", "/api/agreements"),
    ("GET", "/api/agreements"),
    ("GET", "/api/agreements/1"),
    ("PATCH", "/api/agreements/1"),
    ("POST", "/api/opportunities"),
    ("PATCH", "/api/opportunities/1"),
    ("GET", "/api/participants/1"),
    ("PATCH", "/api/participants/1"),
    ("POST", "/api/participants/1/cancel"),
]


@pytest.mark.parametrize("method, path", PROTECTED_ROUTES)
def test_requires_session(anonymous_client, method, path):
    response = anonymous_client.request(method, path, json={})

    assert response.status_code == 401


def test_garbage_cookie_is_401(anonymous_client):
    anonymous_client.cookies.set(auth.COOKIE_NAME, "garbage")

    response = anonymous_client.get("/api/users")

    assert response.status_code == 401


def test_public_route_works_for_anonymous_client(anonymous_client):
    response = anonymous_client.get("/api/organizations")

    assert response.status_code == 200


# liveness/readiness


def test_liveness(anonymous_client):
    response = anonymous_client.get("/api/_health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "live"


def test_readiness(anonymous_client):
    response = anonymous_client.get("/api/_health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.parametrize(
    "dependency, status",
    [
        (routers.dependencies.get_store, "not ready (db: False, email: True)"),
        (routers.dependencies.get_email_sender, "not ready (db: True, email: False)"),
    ],
)
def test_anonymous_client_dependency_down(dependency, status):
    with fastapi.testclient.TestClient(routers.app, base_url="https://testserver") as client:

        class NestedHealth:
            def __init__(self, dependency):
                self.dependency = dependency

            async def get(self) -> bool:
                # DB check is like this due to repository pattern
                return not bool(self.dependency == routers.dependencies.get_store)

        class Deps:
            def __init__(self, dependency):
                self.dependency = dependency
                self.health = NestedHealth(dependency)

            async def check(self) -> bool:
                # Email's check is flatter
                return not bool(self.dependency == routers.dependencies.get_email_sender)

        client.app.dependency_overrides[dependency] = lambda: Deps(dependency)

        response = client.get("/api/_health/ready")
        assert response.status_code == 503
        assert response.json()["status"] == status
