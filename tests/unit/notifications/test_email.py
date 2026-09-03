"""
Coverage for the email notification factory and its file-backed fallback.
SendGrid isn't exercised beyond construction -- doing so would require a live
account -- but the factory's validation of its settings is.
"""

import json

import pytest

from openvols.notifications import email
from openvols.notifications.email.file import FileEmailSender
from openvols.notifications.email.sendgrid import SendGridEmailSender
from tests.unit.notifications.common import get_temp_file_contents


def _message(**overrides) -> email.EmailMessage:
    kwargs = {
        "to": "jane@example.org",
        "subject": "You're registered",
        "html_body": "<p>See you there!</p>",
        "text_body": "See you there!",
    }
    kwargs.update(overrides)
    return email.EmailMessage(**kwargs)


async def test_file_sender_writes_message():
    sender = FileEmailSender()
    await sender.send(_message())

    contents = await get_temp_file_contents(sender)
    assert contents["to"] == "jane@example.org"
    assert contents["subject"] == "You're registered"
    assert contents["html_body"] == "<p>See you there!</p>"
    assert contents["text_body"] == "See you there!"


async def test_file_sender_defaults_to_a_fresh_temp_directory():
    first = FileEmailSender()
    second = FileEmailSender()

    assert first.directory != second.directory


def test_factory_returns_file_sender_by_default():
    sender = email.create_email_sender(email.EmailSettings())
    assert isinstance(sender, FileEmailSender)


def test_factory_returns_sendgrid_sender_when_configured():
    sender = email.create_email_sender(
        email.EmailSettings(backend="sendgrid", sendgrid_api_key="fake-key")
    )
    assert isinstance(sender, SendGridEmailSender)


def test_factory_requires_sendgrid_api_key():
    with pytest.raises(ValueError, match="SENDGRID_API_KEY"):
        email.create_email_sender(email.EmailSettings(backend="sendgrid"))
