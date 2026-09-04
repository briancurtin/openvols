"""
SMS sending abstraction, using a generic Protocol

Callers depend only on openvols.notifications.sms, never on
a specific backend package. SMSSender is a structural typing.Protocol,
so a backend such as openvols.notifications.sms.twilio.TwilioSMSSender or
openvols.notifications.sms.file.FileSMSSender satisfies it without inheritance.
"""

import typing

import pydantic
import pydantic_settings

__all__ = (
    "SMSError",
    "SMSMessage",
    "SMSSender",
    "SMSSettings",
)


class SMSError(Exception):
    """Base for every error an SMSSender raises, regardless of backend"""


class SMSMessage(pydantic.BaseModel):
    """A single SMS to send, populated by the caller from a template"""

    to: str = pydantic.Field(min_length=1)
    body: str = pydantic.Field(min_length=1, max_length=1600)


class SMSSettings(pydantic_settings.BaseSettings):
    """Selects and configures the SMSSender backend, read from the environment"""

    model_config = pydantic_settings.SettingsConfigDict(env_prefix="OPENVOLS_NOTIFICATIONS_SMS_")

    backend: typing.Literal["file", "twilio"] = "file"
    from_number: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""


class SMSSender(typing.Protocol):
    """The single abstraction callers depend on for sending SMS"""

    async def send(self, message: SMSMessage) -> None: ...
