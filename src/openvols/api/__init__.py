import fastapi

app = fastapi.FastAPI(title="OpenVols API")

import openvols.api.routers  # noqa: E402,F401  (registers routes on `app`)
