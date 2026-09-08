"""
Coverage for cookie mechanics in openvols.api.auth.

/api/auth/validate is the only route that issues a cookie until PR 4 adds
require_session to the rest of the authenticated routes, so a temporary probe
route below exercises that dependency end to end.
"""

import http.cookies

import fastapi
import fastapi.testclient
import pytest

from openvols.api import app, auth, routers


@pytest.fixture
def client():
    # https base_url: the default Secure cookie policy means httpx's cookie
    # jar won't echo the cookie back on a later request over plain http.
    with fastapi.testclient.TestClient(routers.app, base_url="https://testserver") as client:
        yield client


@pytest.fixture(autouse=True)
def _reset_auth_settings():
    """Every test starts from the default (Secure) cookie policy."""
    auth.settings.cache_clear()
    yield
    auth.settings.cache_clear()


@pytest.fixture
def user_id(client):
    body = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.org",
        "email_reminders": True,
        "phone": "+12025550182",
        "phone_reminders": True,
    }
    return client.post("/api/users", json=body).json()["id"]


def _cookie(response) -> http.cookies.Morsel:
    jar = http.cookies.SimpleCookie()
    jar.load(response.headers["set-cookie"])
    return jar[auth.COOKIE_NAME]


def test_validate_known_email_issues_session_cookie(client, user_id):
    response = client.get("/api/auth/validate", params={"token": "jane@example.org"})

    assert response.status_code == 200

    cookie = _cookie(response)
    assert cookie.value
    assert cookie["httponly"]
    assert cookie["samesite"] == "lax"
    assert cookie["secure"]
    assert cookie["path"] == "/"
    # 14 days, allowing a few seconds of test execution slack.
    assert abs(int(cookie["max-age"]) - 14 * 24 * 60 * 60) < 5


def test_validate_unknown_email_is_404_with_no_cookie(client):
    response = client.get("/api/auth/validate", params={"token": "nobody@example.org"})

    assert response.status_code == 404
    assert "set-cookie" not in response.headers


def test_validate_respects_insecure_cookie_setting(monkeypatch, client, user_id):
    monkeypatch.setenv("OPENVOLS_API_COOKIE_SECURE", "false")
    auth.settings.cache_clear()

    response = client.get("/api/auth/validate", params={"token": "jane@example.org"})

    cookie = _cookie(response)
    assert not cookie["secure"]
    assert cookie["httponly"]
    assert cookie["samesite"] == "lax"
    assert cookie["path"] == "/"


# ---- Temporary probe route --------------------------------------------------
# No production route requires a session until PR 4; this exercises
# require_session end to end and is removed once a real route does.


@app.get("/api/_test/whoami")
async def _whoami(session: auth.SessionDependency):
    return {"user_id": session.user_id}


def test_issued_token_authenticates(client, user_id):
    client.get("/api/auth/validate", params={"token": "jane@example.org"})

    response = client.get("/api/_test/whoami")

    assert response.status_code == 200
    assert response.json()["user_id"] == user_id


def test_missing_cookie_is_401(client):
    response = client.get("/api/_test/whoami")

    assert response.status_code == 401


def test_garbage_cookie_is_401(client):
    client.cookies.set(auth.COOKIE_NAME, "garbage")

    response = client.get("/api/_test/whoami")

    assert response.status_code == 401
