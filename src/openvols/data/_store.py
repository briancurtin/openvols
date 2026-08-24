"""
Data layer abstraction: the contract every storage backend must satisfy,
the errors it signals, and the settings that select one.

openvols.api depends only on openvols.data (this module's contents, re-exported
via data/__init__.py) -- never on a specific backend package. Repository
protocols are structural (typing.Protocol), so a backend such as
openvols.data.postgres.PostgresStore or openvols.data.memory.MemoryStore
satisfies Store without inheriting from anything defined here.
"""

import builtins
from typing import Literal, Protocol, Self

import pydantic_settings

from openvols import models

# ---- Exceptions --------------------------------------------------------------


class DataError(Exception):
    """Base for every error a Store raises, regardless of backend."""


class NotFoundError(DataError):
    """No record exists for the given id."""

    def __init__(self, resource: str, id: str):
        self.resource = resource
        self.id = id
        super().__init__(f"{resource} {id!r} not found")


class ConflictError(DataError):
    """The requested change conflicts with existing state (e.g. a duplicate)."""


# ---- Configuration -------------------------------------------------------------


class DataSettings(pydantic_settings.BaseSettings):
    """Selects and configures the Store backend, read from the environment."""

    model_config = pydantic_settings.SettingsConfigDict(env_prefix="OPENVOLS_DATA_")

    backend: Literal["memory", "postgres"] = "memory"
    postgres_dsn: str | None = None


# ---- Repository protocols ----------------------------------------------------


class Repository[StoredT, InputT](Protocol):
    """CRUD contract shared by every aggregate's repository."""

    async def create(self, item: InputT) -> StoredT: ...
    async def get(self, id: str) -> StoredT: ...
    # Return type is qualified as `builtins.list` because this method is
    # itself named `list`: Python 3.14's deferred annotation evaluation
    # (PEP 649) resolves a bare `list` here against the class's own
    # namespace once it's fully built, which binds `list` to this method
    # and breaks `typing.get_type_hints()` at runtime, not just type checking.
    async def list(self) -> builtins.list[StoredT]: ...
    async def update(self, id: str, item: InputT) -> StoredT: ...
    async def delete(self, id: str) -> None: ...


class OrganizationRepository(Repository[models.StoredOrganization, models.Organization], Protocol):
    pass


class UserRepository(Repository[models.StoredUser, models.User], Protocol):
    pass


class RoleRepository(Repository[models.StoredRole, models.Role], Protocol):
    pass


class LocationRepository(Repository[models.StoredLocation, models.Location], Protocol):
    pass


class AgreementRepository(Repository[models.StoredAgreement, models.Agreement], Protocol):
    pass


class OpportunityRepository(Repository[models.StoredOpportunity, models.Opportunity], Protocol):
    """
    update() must trigger waitlist promotion when a change (e.g. a capacity
    increase) opens up approved slots. See ParticipantRepository for the
    register/cancel side of the same registration engine.
    """


class ParticipantRepository(Protocol):
    """
    Does not inherit Repository's create(): the initial state (approved vs.
    waitlisted) is a registration engine decision, not a plain insert, so
    creation only happens through register(). get/list/update/delete remain
    plain CRUD -- update() covers things like a manager approving a
    waitlisted participant by hand or marking attendance.

    register() and cancel() are the registration engine described in
    Registration.tla / Waitlist.tla: deciding approved vs. waitlisted on
    registration by id, and promoting waitlisted participants FIFO when a
    cancellation frees a slot.
    """

    async def get(self, id: str) -> models.StoredParticipant: ...
    async def list(self) -> builtins.list[models.StoredParticipant]: ...
    async def update(self, id: str, item: models.Participant) -> models.StoredParticipant: ...
    async def delete(self, id: str) -> None: ...

    async def register(self, user_id: str, opportunity_id: str) -> models.StoredParticipant: ...
    async def cancel(self, participant_id: str) -> None: ...


class Store(Protocol):
    """
    The single abstraction openvols.api depends on. A concrete backend
    (openvols.data.postgres.PostgresStore, openvols.data.memory.MemoryStore, ...)
    satisfies this structurally -- no inheritance required.
    """

    organizations: OrganizationRepository
    users: UserRepository
    roles: RoleRepository
    locations: LocationRepository
    agreements: AgreementRepository
    opportunities: OpportunityRepository
    participants: ParticipantRepository

    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, *exc: object) -> None: ...
