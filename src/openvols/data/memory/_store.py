"""
In-memory Store implementation.

Backs unit tests and local development where a real database isn't
warranted. Every repository lives entirely in process memory -- nothing here
persists across restarts -- and there is no concurrency control beyond
Python's single-threaded event loop, which is sufficient for tests but not a
substitute for a real backend's locking.
"""

import datetime
import uuid
from typing import Self

import pydantic

from openvols import data, models


class _InMemoryRepository[StoredT: models.StoredModel, InputT: pydantic.BaseModel]:
    """Shared CRUD for the aggregates that don't need extra validation or engine logic."""

    def __init__(self, stored_cls: type[StoredT]):
        self._stored_cls = stored_cls
        self._items: dict[str, StoredT] = {}

    async def create(self, item: InputT) -> StoredT:
        now = datetime.datetime.now(datetime.UTC)
        stored = self._stored_cls(
            id=str(uuid.uuid4()), created=now, updated=now, **item.model_dump()
        )
        self._items[stored.id] = stored
        return stored

    async def get(self, id: str) -> StoredT:
        try:
            return self._items[id]
        except KeyError:
            raise data.NotFoundError(self._stored_cls.__name__, id) from None

    async def list(self) -> list[StoredT]:
        return list(self._items.values())

    async def update(self, id: str, item: InputT) -> StoredT:
        existing = await self.get(id)
        stored = self._stored_cls(
            id=id,
            created=existing.created,
            updated=datetime.datetime.now(datetime.UTC),
            **item.model_dump(),
        )
        self._items[id] = stored
        return stored

    async def delete(self, id: str) -> None:
        await self.get(id)
        del self._items[id]


class _RoleRepository:
    """Plain CRUD, plus validating that organization_id/user_id reference real records."""

    def __init__(
        self,
        organizations: _InMemoryRepository[models.StoredOrganization, models.Organization],
        users: _InMemoryRepository[models.StoredUser, models.User],
    ):
        self._repository = _InMemoryRepository(models.StoredRole)
        self._organizations = organizations
        self._users = users

    async def _validate(self, item: models.Role) -> None:
        await self._organizations.get(item.organization_id)
        await self._users.get(item.user_id)

    async def create(self, item: models.Role) -> models.StoredRole:
        await self._validate(item)
        return await self._repository.create(item)

    async def get(self, id: str) -> models.StoredRole:
        return await self._repository.get(id)

    async def list(self) -> list[models.StoredRole]:
        return await self._repository.list()

    async def update(self, id: str, item: models.Role) -> models.StoredRole:
        await self._validate(item)
        return await self._repository.update(id, item)

    async def delete(self, id: str) -> None:
        await self._repository.delete(id)


class _LocationRepository:
    """Plain CRUD, plus validating that organization_id references a real Organization."""

    def __init__(
        self, organizations: _InMemoryRepository[models.StoredOrganization, models.Organization]
    ):
        self._repository = _InMemoryRepository(models.StoredLocation)
        self._organizations = organizations

    async def create(self, item: models.Location) -> models.StoredLocation:
        await self._organizations.get(item.organization_id)
        return await self._repository.create(item)

    async def get(self, id: str) -> models.StoredLocation:
        return await self._repository.get(id)

    async def list(self) -> list[models.StoredLocation]:
        return await self._repository.list()

    async def update(self, id: str, item: models.Location) -> models.StoredLocation:
        await self._organizations.get(item.organization_id)
        return await self._repository.update(id, item)

    async def delete(self, id: str) -> None:
        await self._repository.delete(id)


class _AgreementRepository:
    """Plain CRUD, plus validating that organization_id references a real Organization."""

    def __init__(
        self, organizations: _InMemoryRepository[models.StoredOrganization, models.Organization]
    ):
        self._repository = _InMemoryRepository(models.StoredAgreement)
        self._organizations = organizations

    async def create(self, item: models.Agreement) -> models.StoredAgreement:
        await self._organizations.get(item.organization_id)
        return await self._repository.create(item)

    async def get(self, id: str) -> models.StoredAgreement:
        return await self._repository.get(id)

    async def list(self) -> list[models.StoredAgreement]:
        return await self._repository.list()

    async def update(self, id: str, item: models.Agreement) -> models.StoredAgreement:
        await self._organizations.get(item.organization_id)
        return await self._repository.update(id, item)

    async def delete(self, id: str) -> None:
        await self._repository.delete(id)


class _ParticipantRepository:
    """
    Owns the registration engine: deciding approved vs. waitlisted on
    register(), and promoting waitlisted participants FIFO when capacity
    opens up via cancel() or an opportunity update.
    """

    def __init__(
        self,
        opportunities: _InMemoryRepository[models.StoredOpportunity, models.Opportunity],
        users: _InMemoryRepository[models.StoredUser, models.User],
    ):
        self._opportunities = opportunities
        self._users = users
        self._items: dict[str, models.StoredParticipant] = {}

    async def get(self, id: str) -> models.StoredParticipant:
        try:
            return self._items[id]
        except KeyError:
            raise data.NotFoundError("StoredParticipant", id) from None

    async def list(self) -> list[models.StoredParticipant]:
        return list(self._items.values())

    async def update(self, id: str, item: models.Participant) -> models.StoredParticipant:
        existing = await self.get(id)
        updated = models.StoredParticipant(
            id=id,
            created=existing.created,
            updated=datetime.datetime.now(datetime.UTC),
            **item.model_dump(),
        )
        self._items[id] = updated
        return updated

    async def delete(self, id: str) -> None:
        await self.get(id)
        del self._items[id]

    async def register(self, user_id: str, opportunity_id: str) -> models.StoredParticipant:
        await self._users.get(user_id)
        opportunity = await self._opportunities.get(opportunity_id)

        # A user can re-register after cancelling, so only an active
        # (non-cancelled) registration for this pair counts as a duplicate.
        for participant in self._items.values():
            if (
                participant.user_id == user_id
                and participant.opportunity_id == opportunity_id
                and not participant.cancelled
            ):
                raise data.ConflictError(
                    f"user {user_id!r} is already registered for opportunity {opportunity_id!r}"
                )

        now = datetime.datetime.now(datetime.UTC)
        participant = models.StoredParticipant(
            id=str(uuid.uuid4()),
            created=now,
            updated=now,
            user_id=user_id,
            opportunity_id=opportunity_id,
            approved=self._approved_count(opportunity_id) < opportunity.capacity,
            cancelled=False,
            attended=False,
        )
        self._items[participant.id] = participant
        return participant

    async def cancel(self, participant_id: str) -> None:
        participant = await self.get(participant_id)
        if participant.cancelled:
            return

        was_approved = participant.approved
        self._items[participant_id] = participant.model_copy(
            update={"cancelled": True, "updated": datetime.datetime.now(datetime.UTC)}
        )
        if was_approved:
            await self.promote_waitlist(participant.opportunity_id)

    async def promote_waitlist(self, opportunity_id: str) -> None:
        """
        Approve waitlisted participants FIFO until capacity is filled.
        Called after a cancellation frees a slot, or after an opportunity's
        capacity changes -- the two triggers from technical_design.md.
        """
        opportunity = await self._opportunities.get(opportunity_id)
        open_slots = opportunity.capacity - self._approved_count(opportunity_id)
        if open_slots <= 0:
            return

        now = datetime.datetime.now(datetime.UTC)
        # dict preserves insertion order, so this walk is already FIFO.
        for participant_id, participant in self._items.items():
            if open_slots <= 0:
                break
            if participant.opportunity_id != opportunity_id:
                continue
            if participant.cancelled or participant.approved:
                continue
            self._items[participant_id] = participant.model_copy(
                update={"approved": True, "updated": now}
            )
            open_slots -= 1

    def _approved_count(self, opportunity_id: str) -> int:
        return sum(
            1
            for participant in self._items.values()
            if participant.opportunity_id == opportunity_id
            and not participant.cancelled
            and participant.approved
        )


class _OpportunityRepository:
    """
    Plain CRUD, validating that location_id/contact_id/agreement_ids reference
    real records, plus triggering waitlist promotion on update().
    """

    def __init__(
        self,
        repository: _InMemoryRepository[models.StoredOpportunity, models.Opportunity],
        locations: _InMemoryRepository[models.StoredLocation, models.Location],
        users: _InMemoryRepository[models.StoredUser, models.User],
        agreements: _InMemoryRepository[models.StoredAgreement, models.Agreement],
        participants: _ParticipantRepository,
    ):
        self._repository = repository
        self._locations = locations
        self._users = users
        self._agreements = agreements
        self._participants = participants

    async def _validate(self, item: models.Opportunity) -> None:
        await self._locations.get(item.location_id)
        await self._users.get(item.contact_id)
        for agreement_id in item.agreement_ids:
            await self._agreements.get(agreement_id)

    async def create(self, item: models.Opportunity) -> models.StoredOpportunity:
        await self._validate(item)
        return await self._repository.create(item)

    async def get(self, id: str) -> models.StoredOpportunity:
        return await self._repository.get(id)

    async def list(self) -> list[models.StoredOpportunity]:
        return await self._repository.list()

    async def update(self, id: str, item: models.Opportunity) -> models.StoredOpportunity:
        await self._validate(item)
        updated = await self._repository.update(id, item)
        await self._participants.promote_waitlist(id)
        return updated

    async def delete(self, id: str) -> None:
        await self._repository.delete(id)


class MemoryStore:
    """
    In-memory Store: every repository is backed by a plain dict, and
    nothing persists across process restarts.
    """

    def __init__(self) -> None:
        self.organizations: data.OrganizationRepository = _InMemoryRepository(
            models.StoredOrganization
        )
        self.users: data.UserRepository = _InMemoryRepository(models.StoredUser)
        self.roles: data.RoleRepository = _RoleRepository(self.organizations, self.users)
        self.locations: data.LocationRepository = _LocationRepository(self.organizations)
        self.agreements: data.AgreementRepository = _AgreementRepository(self.organizations)

        # Shared by both repositories below so a capacity change made through
        # opportunities.update() is immediately visible to the registration
        # engine's capacity lookups in participants.register()/promote_waitlist().
        opportunities = _InMemoryRepository(models.StoredOpportunity)
        self.participants: data.ParticipantRepository = _ParticipantRepository(
            opportunities, self.users
        )
        self.opportunities: data.OpportunityRepository = _OpportunityRepository(
            opportunities, self.locations, self.users, self.agreements, self.participants
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None
