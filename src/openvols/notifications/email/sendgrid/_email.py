"""SendGrid-backed EmailSender"""

import asyncio

import sendgrid
from sendgrid.helpers import mail

from openvols.notifications.email._email import EmailError, EmailMessage


class SendGridEmailSender:
    """
    Sends email through the SendGrid HTTP API

    SendGrid's client is synchronous, so send() runs it in a thread to avoid
    blocking the event loop
    """

    def __init__(self, api_key: str, from_email: str):
        self._client = sendgrid.SendGridAPIClient(api_key)
        self._from_email = from_email

    async def __aenter__(self):
        # This is a noop but is necessary to satisfy the protocol because
        # dependency injection in FastAPI uses async context managers
        return self

    async def __aexit__(self, *exc):
        pass

    async def check(self) -> bool:
        """
        Check that the API key is valid by sending a test email to self

        Raises EmailError if the key is invalid or the send fails for any reason
        """
        response = await asyncio.to_thread(self._client.client.user.username.get())

        return bool(response.status_code == 200)

    async def send(self, message: EmailMessage) -> None:
        mail_message = mail.Mail(
            from_email=self._from_email,
            to_emails=message.to,
            subject=message.subject,
            html_content=message.html_body,
            plain_text_content=message.text_body,
        )

        response = await asyncio.to_thread(self._client.send, mail_message)

        if response.status_code >= 400:
            raise EmailError(f"SendGrid returned {response.status_code}: {response.body!r}")
