"""
Coverage for the SMS notification factory and its file-backed fallback.
Twilio isn't exercised beyond construction -- doing so would require a live
account -- but the factory's validation of its settings is.
"""

import asyncio
import json

import pytest

from openvols.notifications import sms
from openvols.notifications.sms.file import FileSMSSender
from openvols.notifications.sms.twilio import TwilioSMSSender
from tests.unit.notifications.common import get_temp_file_contents


def _message(**overrides) -> sms.SMSMessage:
    kwargs = {"to": "+12025550182", "body": "See you tomorrow at 9am!"}
    kwargs.update(overrides)
    return sms.SMSMessage(**kwargs)


async def test_file_sender_writes_message():
    sender = FileSMSSender()
    await sender.send(_message())

    contents = await get_temp_file_contents(sender)
    assert contents["to"] == "+12025550182"
    assert contents["body"] == "See you tomorrow at 9am!"


async def test_file_sender_defaults_to_a_fresh_temp_directory():
    first = FileSMSSender()
    second = FileSMSSender()

    assert first.directory != second.directory


def test_factory_returns_file_sender_by_default():
    sender = sms.create_sms_sender(sms.SMSSettings())
    assert isinstance(sender, FileSMSSender)


def test_factory_returns_twilio_sender_when_configured():
    sender = sms.create_sms_sender(
        sms.SMSSettings(
            backend="twilio",
            twilio_account_sid="AC" + "0" * 32,
            twilio_auth_token="fake-token",
            from_number="+15555550100",
        )
    )
    assert isinstance(sender, TwilioSMSSender)


def test_factory_requires_twilio_credentials():
    with pytest.raises(ValueError, match="TWILIO_ACCOUNT_SID"):
        sms.create_sms_sender(sms.SMSSettings(backend="twilio", from_number="+15555550100"))


def test_factory_requires_twilio_from_number():
    with pytest.raises(ValueError, match="FROM_NUMBER"):
        sms.create_sms_sender(
            sms.SMSSettings(
                backend="twilio", twilio_account_sid="AC" + "0" * 32, twilio_auth_token="fake-token"
            )
        )
