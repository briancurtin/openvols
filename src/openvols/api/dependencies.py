"""FastAPI dependencies shared across openvols.api.routers and openvols.api.auth."""

import typing

import fastapi

from openvols import data


def get_store(request: fastapi.Request) -> data.Store:
    return request.app.state.store


StoreDependency = typing.Annotated[data.Store, fastapi.Depends(get_store)]
