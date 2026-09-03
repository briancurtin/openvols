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


def _message(**overrides) -> email.EmailMessage:
    kwargs = {
        "to": "jane@example.org",
        "subject": "You're registered",
        "html_body": "<p>See you there!</p>",
        "text_body": "See you there!",
    }
    kwargs.update(overrides)
    return email.EmailMessage(**kwargs)


async def test_file_sender_writes_message(tmp_path):
    sender = FileEmailSender(str(tmp_path))
    await sender.send(_message())

    written = list(tmp_path.iterdir())
    assert len(written) == 1
    assert json.loads(written[0].read_text())["to"] == "jane@example.org"


async def test_file_sender_defaults_to_a_fresh_temp_directory():
    first = FileEmailSender()
    second = FileEmailSender()

    assert first.directory != second.directory
    assert first.directory.is_dir()


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
