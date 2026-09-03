"""
File-based EmailSender.

Backs local development and tests where a real email provider isn't
warranted -- see technical_design.md's "Fallback implementation" note.
Nothing here is delivered anywhere; each message is written as a JSON file
for a human or a test to inspect.
"""

import json

from openvols.notifications._common import FileSender
from openvols.notifications.email._email import EmailMessage


class FileEmailSender(FileSender):
    """Writes each EmailMessage as a JSON file in a temporary directory"""

    async def send(self, message: EmailMessage) -> None:
        self.temp_file.write(json.dumps(message.model_dump(), indent=2).encode("utf-8"))
        self.temp_file.flush()
