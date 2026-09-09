"""FastAPI dependencies shared across openvols.api.routers and openvols.api.auth."""

import typing

import fastapi

from openvols import data, notifications


def get_store(request: fastapi.Request) -> data.Store:
    return request.app.state.store


def get_email_sender(request: fastapi.Request) -> notifications.email.EmailSender:
    return request.app.state.email_sender


StoreDependency = typing.Annotated[data.Store, fastapi.Depends(get_store)]
EmailSenderDependency = typing.Annotated[
    notifications.email.EmailSender, fastapi.Depends(get_email_sender)
]
