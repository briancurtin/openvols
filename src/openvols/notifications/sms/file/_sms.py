"""
File-based SMSSender.

Backs local development and tests where a real SMS provider isn't
warranted -- see technical_design.md's "Fallback implementation" note.
Nothing here is delivered anywhere; each message is written as a JSON file
for a human or a test to inspect.
"""

import json

from openvols.notifications._common import FileSender
from openvols.notifications.sms._sms import SMSMessage


class FileSMSSender(FileSender):
    """Writes each SMSMessage as a JSON file in a temporary directory"""

    async def send(self, message: SMSMessage) -> None:
        self.temp_file.write(json.dumps(message.model_dump(), indent=2).encode("utf-8"))
        self.temp_file.flush()
