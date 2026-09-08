"""
Cookie-based authentication for the REST layer.

The cookie holds an opaque session token (see openvols.data.SessionRepository);
this module owns the HTTP-side concerns only -- the flags on the cookie, and
turning a request's cookie into a session or a 401.
"""

import functools
import typing
from datetime import UTC, datetime

import fastapi
import pydantic_settings

from openvols import data, models
from openvols.api import dependencies

__all__ = (
    "COOKIE_NAME",
    "AuthSettings",
    "SessionDependency",
    "clear_session_cookie",
    "require_session",
    "set_session_cookie",
    "settings",
)

COOKIE_NAME = "ov_session"


class AuthSettings(pydantic_settings.BaseSettings):
    """Cookie policy, read from the environment."""

    model_config = pydantic_settings.SettingsConfigDict(env_prefix="OPENVOLS_API_")

    # Secure is the only flag that can be relaxed: local development over
    # plain http can't send a Secure cookie. httponly and samesite are fixed
    # policy -- see the flags on set_session_cookie.
    cookie_secure: bool = True


@functools.lru_cache
def settings() -> AuthSettings:
    return AuthSettings()


def set_session_cookie(response: fastapi.Response, session: models.IssuedSession) -> None:
    """
    Attach a newly issued session to the response.

    * httponly: the token is never readable from JS, which pushes credential
      handling onto the browser and out of the frontend's hands.
    * samesite=lax: a magic-link click is a top-level GET navigation from an
      email client, and the session has to survive it. Strict would not.
    * secure: on by default; OPENVOLS_API_COOKIE_SECURE=false for http dev.
    * max_age derives from the session's own expiry, so the cookie and the row
      can't disagree about when the session ends.
    """
    max_age = int((session.expires - datetime.now(UTC)).total_seconds())

    response.set_cookie(
        key=COOKIE_NAME,
        value=session.token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=settings().cookie_secure,
        path="/",
    )


def clear_session_cookie(response: fastapi.Response) -> None:
    """Expire the cookie. Attributes must match set_session_cookie or browsers keep it."""

    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=settings().cookie_secure,
        path="/",
    )


async def require_session(
    store: dependencies.StoreDependency,
    token: typing.Annotated[str | None, fastapi.Cookie(alias=COOKIE_NAME)] = None,
) -> models.StoredSession:
    if token is None:
        raise fastapi.HTTPException(status_code=401, detail="authentication required")

    try:
        return await store.sessions.get(token)
    except data.InvalidSessionError:
        # Same answer for absent, expired, and forged: nothing about the token
        # is echoed back.
        raise fastapi.HTTPException(status_code=401, detail="authentication required") from None


SessionDependency = typing.Annotated[models.StoredSession, fastapi.Depends(require_session)]
