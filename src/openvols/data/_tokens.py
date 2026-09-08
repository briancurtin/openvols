"""Opaque session token generation and hashing, shared by every Store backend."""

import hashlib
import secrets

__all__ = ("generate", "hashed")


def generate() -> str:
    """A 256-bit URL-safe token, suitable for a cookie value."""

    return secrets.token_urlsafe(32)


def hashed(token: str) -> str:
    """
    The stored form of a token.

    Plain SHA-256 rather than a password KDF: the input is 256 bits of CSPRNG
    output, so there's no low-entropy guess space for a slow hash to protect.
    """

    return hashlib.sha256(token.encode()).hexdigest()
