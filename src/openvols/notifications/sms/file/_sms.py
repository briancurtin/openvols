"""
File-based SMSSender.

Backs local development and tests where a real SMS provider isn't
warranted -- see technical_design.md's "Fallback implementation" note.
Nothing here is delivered anywhere; each message is written as a JSON file
for a human or a test to inspect.
"""

import json
import tempfile

from openvols.notifications.sms._sms import SMSMessage


class FileSMSSender:
    """
    Writes each SMSMessage as a JSON file under `directory`.

    `directory` defaults to a fresh temporary directory when not given,
    since tests and local development don't need the files to persist
    across runs.
    """

    def __init__(self):
        self.directory = tempfile.TemporaryDirectory(prefix="openvols-sms-")
        self.temp_file = tempfile.NamedTemporaryFile(dir=self.directory.name, delete=False)

    def __del__(self):
        self.temp_file.close()
        self.directory.cleanup()

    async def send(self, message: SMSMessage) -> None:
        self.temp_file.write(json.dumps(message.model_dump(), indent=2).encode("utf-8"))
        self.temp_file.flush()
