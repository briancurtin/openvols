"""
Data layer abstraction, using a generic Protocol

Includes the contract every storage backend must satisfy, the errors it signals,
and the settings that select one.

openvols.api depends only on openvols.data (this module's contents, re-exported
via data/__init__.py) -- never on a specific backend package. Repository
protocols are structural using typing.Protocol, so a backend such as
openvols.data.postgres.PostgresStore or openvols.data.memory.MemoryStore
satisfies Store without inheriting from anything defined here.
"""

import builtins
import typing
from datetime import timedelta

import pydantic_settings

from openvols import models

__all__ = (
    "SESSION_LIFETIME",
    "AgreementRepository",
    "ConflictError",
    "DataError",
    "DataSettings",
    "InvalidSessionError",
    "LocationRepository",
    "NotFoundError",
    "OpportunityRepository",
    "OrganizationRepository",
    "ParticipantRepository",
    "Repository",
    "RoleRepository",
    "SessionRepository",
    "Store",
    "UserRepository",
)


# ---- Exceptions --------------------------------------------------------------


class DataError(Exception):
    """Base for every error a Store raises, regardless of backend."""


class NotFoundError(DataError):
    """No record exists for the given id, or other lookup key such as an email."""

    def __init__(self, resource: str, id: int | str):
        self.resource = resource
        self.id = id
        super().__init__(f"{resource} {id!r} not found")


class ConflictError(DataError):
    """The requested change conflicts with existing state (e.g. a duplicate)."""


class InvalidSessionError(DataError):
    """
    The token doesn't identify a live session -- unknown, expired, or deleted.

    Distinct from NotFoundError so the API layer can answer 401 rather than
    404, and deliberately carries no token in its message so a bad token never
    reaches a log line.
    """


# ---- Configuration -------------------------------------------------------------


class DataSettings(pydantic_settings.BaseSettings):
    """Selects and configures the Store backend, read from the environment."""

    model_config = pydantic_settings.SettingsConfigDict(env_prefix="OPENVOLS_DATA_")

    backend: typing.Literal["memory", "postgres"] = "memory"
    postgres_dsn: str = ""


# ---- Repository protocols ----------------------------------------------------


class Repository[StoredT, InputT](typing.Protocol):
    """CRUD contract shared by every aggregate's repository."""

    async def create(self, item: InputT) -> StoredT: ...
    async def get(self, id: int) -> StoredT: ...
    # Return type is qualified as `builtins.list` because this method is
    # itself named `list`: Python 3.14's deferred annotation evaluation
    # (PEP 649) resolves a bare `list` here against the class's own
    # namespace once it's fully built, which binds `list` to this method
    # and breaks `typing.get_type_hints()` at runtime, not just type checking.
    async def list(self) -> builtins.list[StoredT]: ...
    async def update(self, id: int, item: InputT) -> StoredT: ...
    async def delete(self, id: int) -> None: ...


class OrganizationRepository(
    Repository[models.StoredOrganization, models.Organization], typing.Protocol
):
    pass


class UserRepository(Repository[models.StoredUser, models.User], typing.Protocol):
    async def get_by_email(self, email: str) -> models.StoredUser: ...


class RoleRepository(Repository[models.StoredRole, models.Role], typing.Protocol):
    pass


class LocationRepository(Repository[models.StoredLocation, models.Location], typing.Protocol):
    pass


class AgreementRepository(Repository[models.StoredAgreement, models.Agreement], typing.Protocol):
    pass


class OpportunityRepository(
    Repository[models.StoredOpportunity, models.Opportunity], typing.Protocol
):
    """
    update() must trigger waitlist promotion when a change (e.g. a capacity
    increase) opens up approved slots. See ParticipantRepository for the
    register/cancel side of the same registration engine.
    """


class ParticipantRepository(typing.Protocol):
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

    async def get(self, id: int) -> models.StoredParticipant: ...
    async def list(self) -> builtins.list[models.StoredParticipant]: ...
    async def update(self, id: int, item: models.Participant) -> models.StoredParticipant: ...
    async def delete(self, id: int) -> None: ...

    async def register(self, user_id: int, opportunity_id: int) -> models.StoredParticipant: ...
    async def cancel(self, participant_id: int) -> None: ...


SESSION_LIFETIME = timedelta(days=14)


class SessionRepository(typing.Protocol):
    """
    Sessions are addressed by their opaque token, not by id, so this doesn't
    inherit Repository. The store owns token generation and hashing: no caller
    ever holds the material needed to forge one, and both backends agree on the
    stored form.
    """

    async def create(
        self, user_id: int, lifetime: timedelta = SESSION_LIFETIME
    ) -> models.IssuedSession: ...

    async def get(self, token: str) -> models.StoredSession: ...

    async def delete(self, token: str) -> None: ...


class Store(typing.Protocol):
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
    sessions: SessionRepository

    async def __aenter__(self) -> typing.Self: ...
    async def __aexit__(self, *exc: object) -> None: ...
