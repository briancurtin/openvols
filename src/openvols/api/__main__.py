import os
import sys

import uvicorn


def main() -> int:
    """
    Start the OpenVols API service via uvicorn

    - UVICORN_RELOAD is passed to the `reload` argument
    - WEB_CONCURRENCY is mutually exclusive to reload, and sets `workers`
    """
    uvicorn.run(
        "openvols.api:app",
        host="0.0.0.0",
        port=8000,
        reload=bool(os.getenv("UVICORN_RELOAD", False)),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
