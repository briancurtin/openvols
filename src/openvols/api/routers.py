import datetime
import typing
import uuid

import fastapi
import pydantic

import openvols.models

app = fastapi.FastAPI(title="OpenVols API")


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


# Placeholder data used to satisfy response_model validation on read routes until
# a real data layer is wired up. These are not persisted anywhere.

_EXAMPLE_ORGANIZATION = openvols.models.Organization(
    name="Example Organization",
    description="A placeholder organization used until the data layer is wired up.",
    website="https://example.org",
    contact="Jane Doe",
    email="contact@example.org",
    phone="+12025550182",
    private_allowed=False,
    approved=True,
)

_EXAMPLE_USER = openvols.models.User(
    first_name="Jane",
    last_name="Doe",
    email="jane@example.org",
    email_reminders=True,
    phone="+12025550182",
    phone_reminders=True,
)

_EXAMPLE_ROLE = openvols.models.Role(
    organization=_EXAMPLE_ORGANIZATION,
    user=_EXAMPLE_USER,
    type=openvols.models.RoleType.USER,
)

_EXAMPLE_LOCATION = openvols.models.Location(
    organization=_EXAMPLE_ORGANIZATION,
    name="Example Location",
    address="123 Main St",
    city="Springfield",
    state="IL",
    postal_code="62701",
    country="US",
)

_EXAMPLE_AGREEMENT = openvols.models.Agreement(
    organization=_EXAMPLE_ORGANIZATION,
    title="Example Agreement",
    description="A placeholder agreement.",
    content="By participating you agree to the example terms.",
    valid=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
    invalid=datetime.datetime(2027, 1, 1, tzinfo=datetime.UTC),
    cadence=openvols.models.AgreementCadence.PER_OPPORTUNITY,
)

_EXAMPLE_OPPORTUNITY = openvols.models.Opportunity(
    title="Example Opportunity",
    description="A placeholder opportunity.",
    location=_EXAMPLE_LOCATION,
    start=datetime.datetime(2026, 6, 1, 9, 0, tzinfo=datetime.UTC),
    end=datetime.datetime(2026, 6, 1, 12, 0, tzinfo=datetime.UTC),
    public=True,
    open=True,
    cancelled=False,
    completed=False,
    contact=_EXAMPLE_USER,
    capacity=10,
    notes="",
    auto_approve_registrants=True,
    auto_approve_waiters=True,
)

_EXAMPLE_PARTICIPANT = openvols.models.Participant(
    user=_EXAMPLE_USER,
    opportunity=_EXAMPLE_OPPORTUNITY,
    approved=True,
    cancelled=False,
    attended=False,
)


# ---- Organizations ----


@app.post("/api/organizations", response_model=openvols.models.StoredOrganization)
async def create_organization(
    body: typing.Annotated[openvols.models.Organization, fastapi.Body(embed=True)],
):
    return openvols.models.StoredOrganization(id=str(uuid.uuid4()), **body.model_dump())


class ListStoredOrganizations(pydantic.BaseModel):
    """
    Return a list of Organizations, under the 'organizations' key
    """

    organizations: list[openvols.models.StoredOrganization] = []


@app.get("/api/organizations", response_model=ListStoredOrganizations)
async def list_organizations():
    return ListStoredOrganizations()


@app.get(
    "/api/organizations/{organization_id}",
    response_model=openvols.models.StoredOrganization,
)
async def get_organization(organization_id: str):
    return openvols.models.StoredOrganization(
        id=organization_id, **_EXAMPLE_ORGANIZATION.model_dump()
    )


@app.patch(
    "/api/organizations/{organization_id}",
    response_model=openvols.models.StoredOrganization,
)
async def update_organization(
    organization_id: str,
    body: typing.Annotated[openvols.models.Organization, fastapi.Body(embed=True)],
):
    return openvols.models.StoredOrganization(id=organization_id, **body.model_dump())


@app.delete("/api/organizations/{organization_id}")
async def delete_organization(organization_id: str):
    return 200


# ---- Users ----


@app.post("/api/users", response_model=openvols.models.StoredUser)
async def create_user(
    body: typing.Annotated[openvols.models.User, fastapi.Body(embed=True)],
):
    return openvols.models.StoredUser(id=str(uuid.uuid4()), **body.model_dump())


class ListStoredUsers(pydantic.BaseModel):
    users: list[openvols.models.StoredUser] = []


@app.get("/api/users", response_model=ListStoredUsers)
async def list_users():
    return ListStoredUsers()


@app.get("/api/users/{user_id}", response_model=openvols.models.StoredUser)
async def get_user(user_id: str):
    return openvols.models.StoredUser(id=user_id, **_EXAMPLE_USER.model_dump())


@app.patch("/api/users/{user_id}", response_model=openvols.models.StoredUser)
async def update_user(
    user_id: str,
    body: typing.Annotated[openvols.models.User, fastapi.Body(embed=True)],
):
    return openvols.models.StoredUser(id=user_id, **body.model_dump())


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str):
    return 200


# ---- Roles ----


@app.post("/api/roles", response_model=openvols.models.StoredRole)
async def create_role(
    body: typing.Annotated[openvols.models.Role, fastapi.Body(embed=True)],
):
    return openvols.models.StoredRole(id=str(uuid.uuid4()), **body.model_dump())


class ListStoredRoles(pydantic.BaseModel):
    roles: list[openvols.models.StoredRole] = []


@app.get("/api/roles", response_model=ListStoredRoles)
async def list_roles():
    return ListStoredRoles()


@app.get("/api/roles/{role_id}", response_model=openvols.models.StoredRole)
async def get_role(role_id: str):
    return openvols.models.StoredRole(id=role_id, **_EXAMPLE_ROLE.model_dump())


@app.patch("/api/roles/{role_id}", response_model=openvols.models.StoredRole)
async def update_role(
    role_id: str,
    body: typing.Annotated[openvols.models.Role, fastapi.Body(embed=True)],
):
    return openvols.models.StoredRole(id=role_id, **body.model_dump())


@app.delete("/api/roles/{role_id}")
async def delete_role(role_id: str):
    return 200


# ---- Locations ----


@app.post("/api/locations", response_model=openvols.models.StoredLocation)
async def create_location(
    body: typing.Annotated[openvols.models.Location, fastapi.Body(embed=True)],
):
    return openvols.models.StoredLocation(id=str(uuid.uuid4()), **body.model_dump())


class ListStoredLocations(pydantic.BaseModel):
    locations: list[openvols.models.StoredLocation] = []


@app.get("/api/locations", response_model=ListStoredLocations)
async def list_locations():
    return ListStoredLocations()


@app.get("/api/locations/{location_id}", response_model=openvols.models.StoredLocation)
async def get_location(location_id: str):
    return openvols.models.StoredLocation(id=location_id, **_EXAMPLE_LOCATION.model_dump())


@app.patch("/api/locations/{location_id}", response_model=openvols.models.StoredLocation)
async def update_location(
    location_id: str,
    body: typing.Annotated[openvols.models.Location, fastapi.Body(embed=True)],
):
    return openvols.models.StoredLocation(id=location_id, **body.model_dump())


@app.delete("/api/locations/{location_id}")
async def delete_location(location_id: str):
    return 200


# ---- Agreements ----


@app.post("/api/agreements", response_model=openvols.models.StoredAgreement)
async def create_agreement(
    body: typing.Annotated[openvols.models.Agreement, fastapi.Body(embed=True)],
):
    return openvols.models.StoredAgreement(id=str(uuid.uuid4()), **body.model_dump())


class ListStoredAgreements(pydantic.BaseModel):
    agreements: list[openvols.models.StoredAgreement] = []


@app.get("/api/agreements", response_model=ListStoredAgreements)
async def list_agreements():
    return ListStoredAgreements()


@app.get("/api/agreements/{agreement_id}", response_model=openvols.models.StoredAgreement)
async def get_agreement(agreement_id: str):
    return openvols.models.StoredAgreement(id=agreement_id, **_EXAMPLE_AGREEMENT.model_dump())


@app.patch("/api/agreements/{agreement_id}", response_model=openvols.models.StoredAgreement)
async def update_agreement(
    agreement_id: str,
    body: typing.Annotated[openvols.models.Agreement, fastapi.Body(embed=True)],
):
    return openvols.models.StoredAgreement(id=agreement_id, **body.model_dump())


@app.delete("/api/agreements/{agreement_id}")
async def delete_agreement(agreement_id: str):
    return 200


# ---- Opportunities ----


@app.post("/api/opportunities", response_model=openvols.models.StoredOpportunity)
async def create_opportunity(
    body: typing.Annotated[openvols.models.Opportunity, fastapi.Body(embed=True)],
):
    return openvols.models.StoredOpportunity(id=str(uuid.uuid4()), **body.model_dump())


class ListStoredOpportunities(pydantic.BaseModel):
    opportunities: list[openvols.models.StoredOpportunity] = []


@app.get("/api/opportunities", response_model=ListStoredOpportunities)
async def list_opportunities():
    return ListStoredOpportunities()


@app.get(
    "/api/opportunities/{opportunity_id}",
    response_model=openvols.models.StoredOpportunity,
)
async def get_opportunity(opportunity_id: str):
    return openvols.models.StoredOpportunity(id=opportunity_id, **_EXAMPLE_OPPORTUNITY.model_dump())


@app.patch(
    "/api/opportunities/{opportunity_id}",
    response_model=openvols.models.StoredOpportunity,
)
async def update_opportunity(
    opportunity_id: str,
    body: typing.Annotated[openvols.models.Opportunity, fastapi.Body(embed=True)],
):
    return openvols.models.StoredOpportunity(id=opportunity_id, **body.model_dump())


@app.delete("/api/opportunities/{opportunity_id}")
async def delete_opportunity(opportunity_id: str):
    return 200


# ---- Participants ----


@app.post("/api/participants", response_model=openvols.models.StoredParticipant)
async def create_participant(
    body: typing.Annotated[openvols.models.Participant, fastapi.Body(embed=True)],
):
    return openvols.models.StoredParticipant(id=str(uuid.uuid4()), **body.model_dump())


class ListStoredParticipants(pydantic.BaseModel):
    participants: list[openvols.models.StoredParticipant] = []


@app.get("/api/participants", response_model=ListStoredParticipants)
async def list_participants():
    return ListStoredParticipants()


@app.get(
    "/api/participants/{participant_id}",
    response_model=openvols.models.StoredParticipant,
)
async def get_participant(participant_id: str):
    return openvols.models.StoredParticipant(id=participant_id, **_EXAMPLE_PARTICIPANT.model_dump())


@app.patch(
    "/api/participants/{participant_id}",
    response_model=openvols.models.StoredParticipant,
)
async def update_participant(
    participant_id: str,
    body: typing.Annotated[openvols.models.Participant, fastapi.Body(embed=True)],
):
    return openvols.models.StoredParticipant(id=participant_id, **body.model_dump())


@app.delete("/api/participants/{participant_id}")
async def delete_participant(participant_id: str):
    return 200
