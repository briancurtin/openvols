"""FastAPI dependencies shared across openvols.api.routers."""

import fastapi

from openvols import data


def get_store(request: fastapi.Request) -> data.Store:
    return request.app.state.store
