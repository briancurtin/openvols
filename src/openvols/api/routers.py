import typing

import fastapi
import pydantic

app = fastapi.FastAPI()


class LoginEmail(pydantic.BaseModel):
    email: str


@app.post("/api/auth/login")
async def login(body: typing.Annotated[LoginEmail, fastapi.Body(embed=True)]):

    return 200


class TokenParams(pydantic.BaseModel):
    token: str


@app.get("/api/auth/validate")
async def validate_token(params: typing.Annotated[TokenParams, fastapi.Query()]):
    return 200
