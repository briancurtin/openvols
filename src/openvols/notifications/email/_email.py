"""
Email protocol

Callers depend only on openvols.notifications.email not on a specific
backend package.
EmailSender uses structural typing.Protocol, so a backend such as
openvols.notifications.email.sendgrid.SendGridEmailSender or
openvols.notifications.email.file.FileEmailSender satisfies it without
inheritance like an ABC.
"""

import typing

import pydantic
import pydantic_settings


class EmailError(Exception):
    """Base for EmailSender exceptions, regardless of backend"""


class EmailMessage(pydantic.BaseModel):
    """A single email to send, populated by the caller from a template"""

    to: pydantic.EmailStr
    subject: str = pydantic.Field(min_length=1)
    html_body: str = pydantic.Field(min_length=1)
    text_body: str = pydantic.Field(min_length=1)


class EmailSettings(pydantic_settings.BaseSettings):
    """EmailSender backend configurations, read from the environment"""

    model_config = pydantic_settings.SettingsConfigDict(env_prefix="OPENVOLS_NOTIFICATIONS_EMAIL_")

    backend: typing.Literal["file", "sendgrid"] = "file"
    from_email: str = "notifications@openvols.org"
    sendgrid_api_key: str = ""


class EmailSender(typing.Protocol):
    """The abstraction callers depend on for sending email"""

    async def send(self, message: EmailMessage) -> None: ...
