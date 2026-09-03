"""Builds an SmsSender for the backend selected by SmsSettings."""

from openvols.notifications.sms import _sms, file, twilio


def create_sms_sender(settings: _sms.SmsSettings) -> _sms.SmsSender:
    if settings.backend == "file":
        return file.FileSmsSender(settings.file_directory)

    if settings.backend == "twilio":
        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            raise ValueError(
                "OPENVOLS_NOTIFICATIONS_SMS_TWILIO_ACCOUNT_SID and "
                "OPENVOLS_NOTIFICATIONS_SMS_TWILIO_AUTH_TOKEN are required for the twilio backend"
            )

        if not settings.from_number:
            raise ValueError(
                "OPENVOLS_NOTIFICATIONS_SMS_FROM_NUMBER is required for the twilio backend"
            )

        return twilio.TwilioSmsSender(
            settings.twilio_account_sid, settings.twilio_auth_token, settings.from_number
        )

    raise ValueError(f"Unknown SMS backend: {settings.backend!r}")
