import asyncio
import typing

import fastapi
import pydantic

import openvols.models
from openvols.api import app, auth, dependencies


class HealthResponse(pydantic.BaseModel):
    """A health verdict, plus the per-dependency results behind it

    checks is empty for liveness, which depends on nothing.
    """

    status: str
    checks: dict[str, bool] = {}


@app.get("/api/_health/live", response_model=HealthResponse)
async def liveness(response: fastapi.Response):
    """Liveness check"""
    # Prevent callers from caching stale liveness responses
    response.headers["Cache-Control"] = "no-store"
    response.status_code = 200

    return HealthResponse(status="live")


@app.get("/api/_health/ready", response_model=HealthResponse)
async def readiness(
    response: fastapi.Response,
    store: dependencies.StoreDependency,
    email: dependencies.EmailSenderDependency,
):
    """Readiness check"""
    # Prevent callers from caching stale liveness responses
    response.headers["Cache-Control"] = "no-store"

    async with asyncio.TaskGroup() as tg:
        db_task = tg.create_task(store.health.get())
        email_task = tg.create_task(email.check())

    checks = {"db": db_task.result(), "email": email_task.result()}

    if all(checks.values()):
        response.status_code = 200
        status = "ready"
    else:
        response.status_code = 503
        status = "not_ready"

    return HealthResponse(status=status, checks=checks)


class LoginEmail(pydantic.BaseModel):
    email: str


@app.post("/api/auth/login")
async def login(email: LoginEmail):
    return 200


class TokenParams(pydantic.BaseModel):
    token: str


@app.get("/api/auth/validate")
async def validate_token(
    params: typing.Annotated[TokenParams, fastapi.Query()],
    response: fastapi.Response,
    store: dependencies.StoreDependency,
):
    # INTERIM: magic-link tokens don't exist yet, so the token is the user's
    # email address. When https://github.com/briancurtin/openvols/issues/57
    # lands, this line becomes a token lookup; everything below it stays.
    user = await store.users.get_by_email(params.token)

    session = await store.sessions.create(user.id)
    auth.set_session_cookie(response, session)

    return 200


@app.post("/api/auth/logout", status_code=204)
async def logout(
    response: fastapi.Response,
    store: dependencies.StoreDependency,
    token: typing.Annotated[str, fastapi.Cookie(alias=auth.COOKIE_NAME)] = "",
):
    """
    Any caller can call this endpoint to clear their cookie irresspective of token validity
    """
    await store.sessions.delete(token)

    auth.clear_session_cookie(response)


# ---- Organizations ----


@app.post(
    "/api/organizations",
    response_model=openvols.models.StoredOrganization,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def create_organization(
    organization: openvols.models.Organization,
    store: dependencies.StoreDependency,
):
    return await store.organizations.create(organization)


class ListStoredOrganizations(pydantic.BaseModel):
    """
    Return a list of Organizations, under the 'organizations' key
    """

    organizations: list[openvols.models.StoredOrganization] = []


@app.get("/api/organizations", response_model=ListStoredOrganizations)
async def list_organizations(store: dependencies.StoreDependency):
    return ListStoredOrganizations(organizations=await store.organizations.list())


@app.get(
    "/api/organizations/{organization_id}",
    response_model=openvols.models.StoredOrganization,
)
async def get_organization(organization_id: int, store: dependencies.StoreDependency):
    return await store.organizations.get(organization_id)


@app.patch(
    "/api/organizations/{organization_id}",
    response_model=openvols.models.StoredOrganization,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def update_organization(
    organization_id: int,
    organization: openvols.models.Organization,
    store: dependencies.StoreDependency,
):
    return await store.organizations.update(organization_id, organization)


# ---- Users ----


@app.post("/api/users", response_model=openvols.models.StoredUser)
async def create_user(user: openvols.models.User, store: dependencies.StoreDependency):
    return await store.users.create(user)


class ListStoredUsers(pydantic.BaseModel):
    users: list[openvols.models.StoredUser] = []


@app.get(
    "/api/users",
    response_model=ListStoredUsers,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def list_users(store: dependencies.StoreDependency):
    return ListStoredUsers(users=await store.users.list())


@app.get(
    "/api/users/{user_id}",
    response_model=openvols.models.StoredUser,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def get_user(user_id: int, store: dependencies.StoreDependency):
    return await store.users.get(user_id)


@app.patch(
    "/api/users/{user_id}",
    response_model=openvols.models.StoredUser,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def update_user(
    user_id: int, user: openvols.models.User, store: dependencies.StoreDependency
):
    return await store.users.update(user_id, user)


@app.delete("/api/users/{user_id}", dependencies=[fastapi.Depends(auth.require_session)])
async def delete_user(user_id: int, store: dependencies.StoreDependency):
    await store.users.delete(user_id)
    return 200


# ---- Roles ----


@app.post(
    "/api/roles",
    response_model=openvols.models.StoredRole,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def create_role(role: openvols.models.Role, store: dependencies.StoreDependency):
    return await store.roles.create(role)


class ListStoredRoles(pydantic.BaseModel):
    roles: list[openvols.models.StoredRole] = []


@app.get(
    "/api/roles",
    response_model=ListStoredRoles,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def list_roles(store: dependencies.StoreDependency):
    return ListStoredRoles(roles=await store.roles.list())


@app.get(
    "/api/roles/{role_id}",
    response_model=openvols.models.StoredRole,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def get_role(role_id: int, store: dependencies.StoreDependency):
    return await store.roles.get(role_id)


@app.patch(
    "/api/roles/{role_id}",
    response_model=openvols.models.StoredRole,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def update_role(
    role_id: int, role: openvols.models.Role, store: dependencies.StoreDependency
):
    return await store.roles.update(role_id, role)


# ---- Locations ----


@app.post(
    "/api/locations",
    response_model=openvols.models.StoredLocation,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def create_location(location: openvols.models.Location, store: dependencies.StoreDependency):
    return await store.locations.create(location)


class ListStoredLocations(pydantic.BaseModel):
    locations: list[openvols.models.StoredLocation] = []


@app.get("/api/locations", response_model=ListStoredLocations)
async def list_locations(store: dependencies.StoreDependency):
    return ListStoredLocations(locations=await store.locations.list())


@app.get("/api/locations/{location_id}", response_model=openvols.models.StoredLocation)
async def get_location(location_id: int, store: dependencies.StoreDependency):
    return await store.locations.get(location_id)


@app.patch(
    "/api/locations/{location_id}",
    response_model=openvols.models.StoredLocation,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def update_location(
    location_id: int,
    location: openvols.models.Location,
    store: dependencies.StoreDependency,
):
    return await store.locations.update(location_id, location)


# ---- Agreements ----


@app.post(
    "/api/agreements",
    response_model=openvols.models.StoredAgreement,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def create_agreement(
    agreement: openvols.models.Agreement, store: dependencies.StoreDependency
):
    return await store.agreements.create(agreement)


class ListStoredAgreements(pydantic.BaseModel):
    agreements: list[openvols.models.StoredAgreement] = []


@app.get(
    "/api/agreements",
    response_model=ListStoredAgreements,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def list_agreements(store: dependencies.StoreDependency):
    return ListStoredAgreements(agreements=await store.agreements.list())


@app.get(
    "/api/agreements/{agreement_id}",
    response_model=openvols.models.StoredAgreement,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def get_agreement(agreement_id: int, store: dependencies.StoreDependency):
    return await store.agreements.get(agreement_id)


@app.patch(
    "/api/agreements/{agreement_id}",
    response_model=openvols.models.StoredAgreement,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def update_agreement(
    agreement_id: int,
    agreement: openvols.models.Agreement,
    store: dependencies.StoreDependency,
):
    return await store.agreements.update(agreement_id, agreement)


# ---- Opportunities ----


@app.post(
    "/api/opportunities",
    response_model=openvols.models.StoredOpportunity,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def create_opportunity(
    opportunity: openvols.models.Opportunity,
    store: dependencies.StoreDependency,
):
    return await store.opportunities.create(opportunity)


class ListStoredOpportunities(pydantic.BaseModel):
    opportunities: list[openvols.models.StoredOpportunity] = []


@app.get("/api/opportunities", response_model=ListStoredOpportunities)
async def list_opportunities(store: dependencies.StoreDependency):
    return ListStoredOpportunities(opportunities=await store.opportunities.list())


@app.get(
    "/api/opportunities/{opportunity_id}",
    response_model=openvols.models.StoredOpportunity,
)
async def get_opportunity(opportunity_id: int, store: dependencies.StoreDependency):
    return await store.opportunities.get(opportunity_id)


@app.patch(
    "/api/opportunities/{opportunity_id}",
    response_model=openvols.models.StoredOpportunity,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def update_opportunity(
    opportunity_id: int,
    opportunity: openvols.models.Opportunity,
    store: dependencies.StoreDependency,
):
    # A capacity increase here can open up approved slots -- the Store is
    # responsible for promoting waitlisted participants to fill them.
    return await store.opportunities.update(opportunity_id, opportunity)


# ---- Participants ----


class RegisterParticipant(pydantic.BaseModel):
    """Request body to register a user's participation in an opportunity."""

    user_id: int
    opportunity_id: int


@app.post("/api/participants", response_model=openvols.models.StoredParticipant)
async def create_participant(participant: RegisterParticipant, store: dependencies.StoreDependency):
    # Registration decides approved vs. waitlisted based on capacity, so it
    # goes through register() rather than a plain create().
    return await store.participants.register(participant.user_id, participant.opportunity_id)


class ListStoredParticipants(pydantic.BaseModel):
    participants: list[openvols.models.StoredParticipant] = []


@app.get("/api/participants", response_model=ListStoredParticipants)
async def list_participants(store: dependencies.StoreDependency):
    return ListStoredParticipants(participants=await store.participants.list())


@app.get(
    "/api/participants/{participant_id}",
    response_model=openvols.models.StoredParticipant,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def get_participant(participant_id: int, store: dependencies.StoreDependency):
    return await store.participants.get(participant_id)


@app.patch(
    "/api/participants/{participant_id}",
    response_model=openvols.models.StoredParticipant,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def update_participant(
    participant_id: int,
    participant: openvols.models.Participant,
    store: dependencies.StoreDependency,
):
    return await store.participants.update(participant_id, participant)


@app.post(
    "/api/participants/{participant_id}/cancel",
    response_model=openvols.models.StoredParticipant,
    dependencies=[fastapi.Depends(auth.require_session)],
)
async def cancel_participant(participant_id: int, store: dependencies.StoreDependency):
    # Cancelling an approved participant can free a slot -- the Store is
    # responsible for promoting the next waitlisted participant, FIFO.
    await store.participants.cancel(participant_id)
    return await store.participants.get(participant_id)
