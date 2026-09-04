"""Public interface for the SendGrid EmailSender backend."""

from openvols.notifications.email.sendgrid._email import SendGridEmailSender

__all__ = ["SendGridEmailSender"]
