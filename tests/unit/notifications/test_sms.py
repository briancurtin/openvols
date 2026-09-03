"""
Coverage for the SMS notification factory and its file-backed fallback.
Twilio isn't exercised beyond construction -- doing so would require a live
account -- but the factory's validation of its settings is.
"""

import json

import pytest

from openvols.notifications import sms
from openvols.notifications.sms.file import FileSmsSender
from openvols.notifications.sms.twilio import TwilioSmsSender


def _message(**overrides) -> sms.SmsMessage:
    kwargs = {"to": "+12025550182", "body": "See you tomorrow at 9am!"}
    kwargs.update(overrides)
    return sms.SmsMessage(**kwargs)


async def test_file_sender_writes_message(tmp_path):
    sender = FileSmsSender(str(tmp_path))
    await sender.send(_message())

    written = list(tmp_path.iterdir())
    assert len(written) == 1
    assert json.loads(written[0].read_text())["to"] == "+12025550182"


async def test_file_sender_defaults_to_a_fresh_temp_directory():
    first = FileSmsSender()
    second = FileSmsSender()

    assert first.directory != second.directory
    assert first.directory.is_dir()


def test_factory_returns_file_sender_by_default():
    sender = sms.create_sms_sender(sms.SmsSettings())
    assert isinstance(sender, FileSmsSender)


def test_factory_returns_twilio_sender_when_configured():
    sender = sms.create_sms_sender(
        sms.SmsSettings(
            backend="twilio",
            twilio_account_sid="AC" + "0" * 32,
            twilio_auth_token="fake-token",
            from_number="+15555550100",
        )
    )
    assert isinstance(sender, TwilioSmsSender)


def test_factory_requires_twilio_credentials():
    with pytest.raises(ValueError, match="TWILIO_ACCOUNT_SID"):
        sms.create_sms_sender(sms.SmsSettings(backend="twilio", from_number="+15555550100"))


def test_factory_requires_twilio_from_number():
    with pytest.raises(ValueError, match="FROM_NUMBER"):
        sms.create_sms_sender(
            sms.SmsSettings(
                backend="twilio", twilio_account_sid="AC" + "0" * 32, twilio_auth_token="fake-token"
            )
        )
