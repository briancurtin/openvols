import asyncio
import json


def _get_temp_file_contents(path) -> dict:
    """Return the JSON contents of the temp test file"""
    with open(path, "r", encoding="utf-8") as f:
        return json.loads(f.read())


async def get_temp_file_contents(sender) -> dict:
    """Return the JSON contents of the sender's temp file"""
    return await asyncio.get_running_loop().run_in_executor(
        None, _get_temp_file_contents, sender.temp_file.name
    )
