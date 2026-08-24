import typing

import fastapi
import pydantic

import openvols.models
from openvols import data
from openvols.api import app, dependencies

StoreDependency = typing.Annotated[data.Store, fastapi.Depends(dependencies.get_store)]


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


# ---- Organizations ----


@app.post("/api/organizations", response_model=openvols.models.StoredOrganization)
async def create_organization(
    body: typing.Annotated[openvols.models.Organization, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    return await store.organizations.create(body)


class ListStoredOrganizations(pydantic.BaseModel):
    """
    Return a list of Organizations, under the 'organizations' key
    """

    organizations: list[openvols.models.StoredOrganization] = []


@app.get("/api/organizations", response_model=ListStoredOrganizations)
async def list_organizations(store: StoreDependency):
    return ListStoredOrganizations(organizations=await store.organizations.list())


@app.get(
    "/api/organizations/{organization_id}",
    response_model=openvols.models.StoredOrganization,
)
async def get_organization(organization_id: int, store: StoreDependency):
    return await store.organizations.get(organization_id)


@app.patch(
    "/api/organizations/{organization_id}",
    response_model=openvols.models.StoredOrganization,
)
async def update_organization(
    organization_id: int,
    body: typing.Annotated[openvols.models.Organization, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    return await store.organizations.update(organization_id, body)


@app.delete("/api/organizations/{organization_id}")
async def delete_organization(organization_id: int, store: StoreDependency):
    await store.organizations.delete(organization_id)
    return 200


# ---- Users ----


@app.post("/api/users", response_model=openvols.models.StoredUser)
async def create_user(
    body: typing.Annotated[openvols.models.User, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    return await store.users.create(body)


class ListStoredUsers(pydantic.BaseModel):
    users: list[openvols.models.StoredUser] = []


@app.get("/api/users", response_model=ListStoredUsers)
async def list_users(store: StoreDependency):
    return ListStoredUsers(users=await store.users.list())


@app.get("/api/users/{user_id}", response_model=openvols.models.StoredUser)
async def get_user(user_id: int, store: StoreDependency):
    return await store.users.get(user_id)


@app.patch("/api/users/{user_id}", response_model=openvols.models.StoredUser)
async def update_user(
    user_id: int,
    body: typing.Annotated[openvols.models.User, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    return await store.users.update(user_id, body)


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, store: StoreDependency):
    await store.users.delete(user_id)
    return 200


# ---- Roles ----


@app.post("/api/roles", response_model=openvols.models.StoredRole)
async def create_role(
    body: typing.Annotated[openvols.models.Role, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    return await store.roles.create(body)


class ListStoredRoles(pydantic.BaseModel):
    roles: list[openvols.models.StoredRole] = []


@app.get("/api/roles", response_model=ListStoredRoles)
async def list_roles(store: StoreDependency):
    return ListStoredRoles(roles=await store.roles.list())


@app.get("/api/roles/{role_id}", response_model=openvols.models.StoredRole)
async def get_role(role_id: int, store: StoreDependency):
    return await store.roles.get(role_id)


@app.patch("/api/roles/{role_id}", response_model=openvols.models.StoredRole)
async def update_role(
    role_id: int,
    body: typing.Annotated[openvols.models.Role, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    return await store.roles.update(role_id, body)


@app.delete("/api/roles/{role_id}")
async def delete_role(role_id: int, store: StoreDependency):
    await store.roles.delete(role_id)
    return 200


# ---- Locations ----


@app.post("/api/locations", response_model=openvols.models.StoredLocation)
async def create_location(
    body: typing.Annotated[openvols.models.Location, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    return await store.locations.create(body)


class ListStoredLocations(pydantic.BaseModel):
    locations: list[openvols.models.StoredLocation] = []


@app.get("/api/locations", response_model=ListStoredLocations)
async def list_locations(store: StoreDependency):
    return ListStoredLocations(locations=await store.locations.list())


@app.get("/api/locations/{location_id}", response_model=openvols.models.StoredLocation)
async def get_location(location_id: int, store: StoreDependency):
    return await store.locations.get(location_id)


@app.patch("/api/locations/{location_id}", response_model=openvols.models.StoredLocation)
async def update_location(
    location_id: int,
    body: typing.Annotated[openvols.models.Location, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    return await store.locations.update(location_id, body)


@app.delete("/api/locations/{location_id}")
async def delete_location(location_id: int, store: StoreDependency):
    await store.locations.delete(location_id)
    return 200


# ---- Agreements ----


@app.post("/api/agreements", response_model=openvols.models.StoredAgreement)
async def create_agreement(
    body: typing.Annotated[openvols.models.Agreement, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    return await store.agreements.create(body)


class ListStoredAgreements(pydantic.BaseModel):
    agreements: list[openvols.models.StoredAgreement] = []


@app.get("/api/agreements", response_model=ListStoredAgreements)
async def list_agreements(store: StoreDependency):
    return ListStoredAgreements(agreements=await store.agreements.list())


@app.get("/api/agreements/{agreement_id}", response_model=openvols.models.StoredAgreement)
async def get_agreement(agreement_id: int, store: StoreDependency):
    return await store.agreements.get(agreement_id)


@app.patch("/api/agreements/{agreement_id}", response_model=openvols.models.StoredAgreement)
async def update_agreement(
    agreement_id: int,
    body: typing.Annotated[openvols.models.Agreement, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    return await store.agreements.update(agreement_id, body)


@app.delete("/api/agreements/{agreement_id}")
async def delete_agreement(agreement_id: int, store: StoreDependency):
    await store.agreements.delete(agreement_id)
    return 200


# ---- Opportunities ----


@app.post("/api/opportunities", response_model=openvols.models.StoredOpportunity)
async def create_opportunity(
    body: typing.Annotated[openvols.models.Opportunity, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    return await store.opportunities.create(body)


class ListStoredOpportunities(pydantic.BaseModel):
    opportunities: list[openvols.models.StoredOpportunity] = []


@app.get("/api/opportunities", response_model=ListStoredOpportunities)
async def list_opportunities(store: StoreDependency):
    return ListStoredOpportunities(opportunities=await store.opportunities.list())


@app.get(
    "/api/opportunities/{opportunity_id}",
    response_model=openvols.models.StoredOpportunity,
)
async def get_opportunity(opportunity_id: int, store: StoreDependency):
    return await store.opportunities.get(opportunity_id)


@app.patch(
    "/api/opportunities/{opportunity_id}",
    response_model=openvols.models.StoredOpportunity,
)
async def update_opportunity(
    opportunity_id: int,
    body: typing.Annotated[openvols.models.Opportunity, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    # A capacity increase here can open up approved slots -- the Store is
    # responsible for promoting waitlisted participants to fill them.
    return await store.opportunities.update(opportunity_id, body)


@app.delete("/api/opportunities/{opportunity_id}")
async def delete_opportunity(opportunity_id: int, store: StoreDependency):
    await store.opportunities.delete(opportunity_id)
    return 200


# ---- Participants ----


class RegisterParticipant(pydantic.BaseModel):
    """Request body to register a user's participation in an opportunity."""

    user_id: int
    opportunity_id: int


@app.post("/api/participants", response_model=openvols.models.StoredParticipant)
async def create_participant(
    body: typing.Annotated[RegisterParticipant, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    # Registration decides approved vs. waitlisted based on capacity, so it
    # goes through register() rather than a plain create().
    return await store.participants.register(body.user_id, body.opportunity_id)


class ListStoredParticipants(pydantic.BaseModel):
    participants: list[openvols.models.StoredParticipant] = []


@app.get("/api/participants", response_model=ListStoredParticipants)
async def list_participants(store: StoreDependency):
    return ListStoredParticipants(participants=await store.participants.list())


@app.get(
    "/api/participants/{participant_id}",
    response_model=openvols.models.StoredParticipant,
)
async def get_participant(participant_id: int, store: StoreDependency):
    return await store.participants.get(participant_id)


@app.patch(
    "/api/participants/{participant_id}",
    response_model=openvols.models.StoredParticipant,
)
async def update_participant(
    participant_id: int,
    body: typing.Annotated[openvols.models.Participant, fastapi.Body(embed=True)],
    store: StoreDependency,
):
    return await store.participants.update(participant_id, body)


@app.post(
    "/api/participants/{participant_id}/cancel",
    response_model=openvols.models.StoredParticipant,
)
async def cancel_participant(participant_id: int, store: StoreDependency):
    # Cancelling an approved participant can free a slot -- the Store is
    # responsible for promoting the next waitlisted participant, FIFO.
    await store.participants.cancel(participant_id)
    return await store.participants.get(participant_id)


@app.delete("/api/participants/{participant_id}")
async def delete_participant(participant_id: int, store: StoreDependency):
    await store.participants.delete(participant_id)
    return 200
