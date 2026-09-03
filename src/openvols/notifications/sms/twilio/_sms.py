"""Twilio-backed SmsSender."""

import asyncio

import twilio.rest

from openvols.notifications.sms._sms import SmsMessage


class TwilioSmsSender:
    """
    Sends SMS through the Twilio REST API.

    Twilio's client is synchronous, so send() runs it in a thread to avoid
    blocking the event loop.
    """

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self._client = twilio.rest.Client(account_sid, auth_token)
        self._from_number = from_number

    async def send(self, message: SmsMessage) -> None:
        await asyncio.to_thread(
            self._client.messages.create,
            to=message.to,
            from_=self._from_number,
            body=message.body,
        )
