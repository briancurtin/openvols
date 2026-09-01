import contextlib
import typing

import fastapi
import fastapi.responses
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from openvols import data, telemetry


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI) -> typing.AsyncIterator[None]:
    async with data.create_store(data.DataSettings()) as store:
        app.state.store = store
        yield


app = fastapi.FastAPI(title="OpenVols API", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(
    app, tracer_provider=telemetry.tracer_provider, meter_provider=telemetry.meter_provider
)


@app.exception_handler(data.NotFoundError)
async def handle_not_found(
    request: fastapi.Request, exc: data.NotFoundError
) -> fastapi.responses.JSONResponse:
    return fastapi.responses.JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(data.ConflictError)
async def handle_conflict(
    request: fastapi.Request, exc: data.ConflictError
) -> fastapi.responses.JSONResponse:
    return fastapi.responses.JSONResponse(status_code=409, content={"detail": str(exc)})


import openvols.api.routers  # noqa: E402,F401  (registers routes on `app`)
