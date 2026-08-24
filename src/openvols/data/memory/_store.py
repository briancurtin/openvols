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
    """Shared CRUD for the aggregates that don't need registration-engine logic."""

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


class _ParticipantRepository:
    """
    Owns the registration engine: deciding approved vs. waitlisted on
    register(), and promoting waitlisted participants FIFO when capacity
    opens up via cancel() or an opportunity update.

    StoredParticipant embeds full User/Opportunity snapshots rather than
    ids (see openvols.models), so a separate id index is kept internally to
    know which opportunity each participant belongs to.
    """

    def __init__(
        self,
        opportunities: _InMemoryRepository[models.StoredOpportunity, models.Opportunity],
        users: _InMemoryRepository[models.StoredUser, models.User],
    ):
        self._opportunities = opportunities
        self._users = users
        self._items: dict[str, models.StoredParticipant] = {}
        self._opportunity_id_by_participant: dict[str, str] = {}

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
        del self._opportunity_id_by_participant[id]

    async def register(self, user_id: str, opportunity_id: str) -> models.StoredParticipant:
        user = await self._users.get(user_id)
        opportunity = await self._opportunities.get(opportunity_id)
        now = datetime.datetime.now(datetime.UTC)

        participant = models.StoredParticipant(
            id=str(uuid.uuid4()),
            created=now,
            updated=now,
            user=models.User(**user.model_dump(exclude={"id", "created", "updated"})),
            opportunity=models.Opportunity(
                **opportunity.model_dump(exclude={"id", "created", "updated"})
            ),
            approved=self._approved_count(opportunity_id) < opportunity.capacity,
            cancelled=False,
            attended=False,
        )
        self._items[participant.id] = participant
        self._opportunity_id_by_participant[participant.id] = opportunity_id
        return participant

    async def cancel(self, participant_id: str) -> None:
        participant = await self.get(participant_id)
        if participant.cancelled:
            return

        opportunity_id = self._opportunity_id_by_participant[participant_id]
        was_approved = participant.approved
        self._items[participant_id] = participant.model_copy(
            update={"cancelled": True, "updated": datetime.datetime.now(datetime.UTC)}
        )
        if was_approved:
            await self.promote_waitlist(opportunity_id)

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
        registrations = self._opportunity_id_by_participant.items()
        for participant_id, associated_opportunity_id in registrations:
            if open_slots <= 0:
                break
            if associated_opportunity_id != opportunity_id:
                continue
            participant = self._items[participant_id]
            if participant.cancelled or participant.approved:
                continue
            self._items[participant_id] = participant.model_copy(
                update={"approved": True, "updated": now}
            )
            open_slots -= 1

    def _approved_count(self, opportunity_id: str) -> int:
        registrations = self._opportunity_id_by_participant.items()
        return sum(
            1
            for participant_id, associated_opportunity_id in registrations
            if associated_opportunity_id == opportunity_id
            and not self._items[participant_id].cancelled
            and self._items[participant_id].approved
        )


class _OpportunityRepository:
    """Wraps generic CRUD for Opportunities, adding waitlist promotion on update()."""

    def __init__(
        self,
        repository: _InMemoryRepository[models.StoredOpportunity, models.Opportunity],
        participants: _ParticipantRepository,
    ):
        self._repository = repository
        self._participants = participants

    async def create(self, item: models.Opportunity) -> models.StoredOpportunity:
        return await self._repository.create(item)

    async def get(self, id: str) -> models.StoredOpportunity:
        return await self._repository.get(id)

    async def list(self) -> list[models.StoredOpportunity]:
        return await self._repository.list()

    async def update(self, id: str, item: models.Opportunity) -> models.StoredOpportunity:
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
        self.roles: data.RoleRepository = _InMemoryRepository(models.StoredRole)
        self.locations: data.LocationRepository = _InMemoryRepository(models.StoredLocation)
        self.agreements: data.AgreementRepository = _InMemoryRepository(models.StoredAgreement)

        opportunities = _InMemoryRepository(models.StoredOpportunity)
        self.participants: data.ParticipantRepository = _ParticipantRepository(
            opportunities, self.users
        )
        self.opportunities: data.OpportunityRepository = _OpportunityRepository(
            opportunities, self.participants
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None
