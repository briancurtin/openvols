"""
File-based SMSSender.

Backs local development and tests where a real SMS provider isn't
warranted -- see technical_design.md's "Fallback implementation" note.
Nothing here is delivered anywhere; each message is written as a JSON file
for a human or a test to inspect.
"""

import abc
import tempfile


class FileSender(abc.ABC):
    """Writes each message type as a JSON file in a temporary directory"""

    def __init__(self):
        self.directory = tempfile.TemporaryDirectory(prefix="openvols-sms-")
        # SIM115 wants us to use a context manager, but we keep it open and close on __del__
        self.temp_file = tempfile.NamedTemporaryFile(dir=self.directory.name, delete=False)  # noqa: SIM115

    def __del__(self):
        self.temp_file.close()
        self.directory.cleanup()

    @abc.abstractmethod
    async def send(self, message) -> None: ...
