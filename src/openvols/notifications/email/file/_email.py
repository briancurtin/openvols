"""
File-based EmailSender for local development and tests without a real provider
"""

import json

from openvols.notifications._common import FileSender
from openvols.notifications.email._email import EmailMessage


class FileEmailSender(FileSender):
    """Writes each EmailMessage as a JSON file in a temporary directory"""

    async def send(self, message: EmailMessage) -> None:
        self.temp_file.write(json.dumps(message.model_dump(), indent=2).encode("utf-8"))
        self.temp_file.flush()
