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
