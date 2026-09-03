"""
File-based SmsSender.

Backs local development and tests where a real SMS provider isn't
warranted -- see technical_design.md's "Fallback implementation" note.
Nothing here is delivered anywhere; each message is written as a JSON file
for a human or a test to inspect.
"""

import json
import tempfile
import uuid
from pathlib import Path

from openvols.notifications.sms._sms import SmsMessage


class FileSmsSender:
    """
    Writes each SmsMessage as a JSON file under `directory`.

    `directory` defaults to a fresh temporary directory when not given,
    since tests and local development don't need the files to persist
    across runs.
    """

    def __init__(self, directory: str = ""):
        self.directory = (
            Path(directory) if directory else Path(tempfile.mkdtemp(prefix="openvols-sms-"))
        )
        self.directory.mkdir(parents=True, exist_ok=True)

    async def send(self, message: SmsMessage) -> None:
        path = self.directory / f"{uuid.uuid4()}.json"
        path.write_text(json.dumps(message.model_dump(), indent=2))
