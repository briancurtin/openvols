"""
File-based Sender for Email and SMS subclasses

Used for local development and tests without a real provider
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
