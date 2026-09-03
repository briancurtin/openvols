"""Builds an EmailSender for the backend selected by EmailSettings."""

from openvols.notifications.email import _email, file, sendgrid


def create_email_sender(settings: _email.EmailSettings) -> _email.EmailSender:
    if settings.backend == "file":
        return file.FileEmailSender(settings.file_directory)

    if settings.backend == "sendgrid":
        if not settings.sendgrid_api_key:
            raise ValueError(
                "OPENVOLS_NOTIFICATIONS_EMAIL_SENDGRID_API_KEY is required for the sendgrid backend"
            )

        return sendgrid.SendGridEmailSender(settings.sendgrid_api_key, settings.from_email)

    raise ValueError(f"Unknown email backend: {settings.backend!r}")
