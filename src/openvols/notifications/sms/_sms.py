"""
SMS sending abstraction, using a generic Protocol.

Includes the contract every SMS backend must satisfy, the errors it
signals, and the settings that select one.

Callers -- openvols.api and openvols.notifications above all -- depend only
on openvols.notifications.sms (this module's contents, re-exported via
sms/__init__.py), never on a specific backend package. SmsSender is a
structural typing.Protocol, so a backend such as
openvols.notifications.sms.twilio.TwilioSmsSender or
openvols.notifications.sms.file.FileSmsSender satisfies it without
inheriting from anything defined here.
"""

import typing

import pydantic
import pydantic_settings


class SmsError(Exception):
    """Base for every error an SmsSender raises, regardless of backend."""


class SmsMessage(pydantic.BaseModel):
    """A single SMS to send, populated by the caller from a template."""

    to: str = pydantic.Field(min_length=1)
    body: str = pydantic.Field(min_length=1, max_length=1600)


class SmsSettings(pydantic_settings.BaseSettings):
    """Selects and configures the SmsSender backend, read from the environment."""

    model_config = pydantic_settings.SettingsConfigDict(env_prefix="OPENVOLS_NOTIFICATIONS_SMS_")

    backend: typing.Literal["file", "twilio"] = "file"
    from_number: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    file_directory: str = ""


class SmsSender(typing.Protocol):
    """The single abstraction callers depend on for sending SMS."""

    async def send(self, message: SmsMessage) -> None: ...
