"""
File-based SMSSender for local development and tests without a real provider
"""

import json

from openvols.notifications._common import FileSender
from openvols.notifications.sms._sms import SMSMessage


class FileSMSSender(FileSender):
    """Writes each SMSMessage as a JSON file in a temporary directory"""

    async def send(self, message: SMSMessage) -> None:
        self.temp_file.write(json.dumps(message.model_dump(), indent=2).encode("utf-8"))
        self.temp_file.flush()
