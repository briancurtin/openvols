from openvols.notifications.sms import _sms, file, twilio

__all__ = ["create_sms_sender"]


def create_sms_sender(settings: _sms.SMSSettings) -> _sms.SMSSender:
    """Returns an SMSSender for the backend configured by SMSSettings"""
    if settings.backend == "file":
        return file.FileSMSSender()

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

        return twilio.TwilioSMSSender(
            settings.twilio_account_sid, settings.twilio_auth_token, settings.from_number
        )

    raise ValueError(f"Unknown SMS backend: {settings.backend!r}")
