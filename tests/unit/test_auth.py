"""
Coverage for cookie mechanics in openvols.api.auth.

require_session itself is exercised end to end via the protected routes in
tests/unit/test_routes.py; this module covers the cookie flags /api/auth/validate
sets.
"""

import http.cookies

import fastapi.testclient
import pytest

from openvols.api import auth, routers


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
