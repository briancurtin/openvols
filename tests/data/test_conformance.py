"""
Behavior tests run against every Store backend via the `store` fixture
(see conftest.py). The point isn't "does it not crash" -- it's catching any
place a backend's actual behavior diverges from what Store promises, since
openvols.api is written against the abstraction, not a specific backend.
"""

from datetime import UTC, datetime

import pytest

from openvols import models
from openvols.data import ConflictError, NotFoundError
from openvols.data.postgres import PostgresStore


def _agreement(organization_id: int) -> models.Agreement:
    return models.Agreement(
        organization_id=organization_id,
        title="Volunteer Waiver",
        description="Standard liability waiver",
        content="By participating in this opportunity you agree to the terms outlined here.",
        valid=datetime(2026, 1, 1, tzinfo=UTC),
        invalid=datetime(2027, 1, 1, tzinfo=UTC),
        cadence=models.AgreementCadence.PER_OPPORTUNITY,
    )


def _organization() -> models.Organization:
    return models.Organization(
        name="Example Organization",
        description="A volunteer organization",
        website="https://example.org",
        contact="jane@example.org",
        email="contact@example.org",
        phone="+12025550182",
        private_allowed=False,
        approved=True,
    )


def _user(email: str) -> models.User:
    return models.User(
        first_name="Jane",
        last_name="Doe",
        email=email,
        email_reminders=True,
        phone="+12025550182",
        phone_reminders=True,
    )


def _location(organization_id: int) -> models.Location:
    return models.Location(
        organization_id=organization_id,
        name="Community Center",
        address="123 Main St",
        city="Springfield",
        state="IL",
        postal_code="62701",
        country="US",
    )


def _opportunity(location_id: int, contact_id: int, capacity: int) -> models.Opportunity:
    return models.Opportunity(
        title="Park Cleanup",
        description=(
            "Join volunteers for a community cleanup at the park: picking up litter, "
            "weeding garden beds, repainting benches, and clearing walking trails."
        ),
        location_id=location_id,
        start=datetime(2026, 6, 1, 9, tzinfo=UTC),
        end=datetime(2026, 6, 1, 12, tzinfo=UTC),
        public=True,
        open=True,
        cancelled=False,
        completed=False,
        contact_id=contact_id,
        capacity=capacity,
        notes="",
        auto_approve_registrants=True,
        auto_approve_waiters=True,
    )


async def _make_opportunity(store, capacity: int) -> models.StoredOpportunity:
    """Set up the organization/location/contact an opportunity needs, and create it."""
    organization = await store.organizations.create(_organization())
    location = await store.locations.create(_location(organization.id))
    contact = await store.users.create(_user(f"contact-{organization.id}@example.org"))

    return await store.opportunities.create(_opportunity(location.id, contact.id, capacity))


# ---- Plain CRUD --------------------------------------------------------------


async def test_organization_crud_lifecycle(store):
    created = await store.organizations.create(_organization())
    assert created.id

    fetched = await store.organizations.get(created.id)
    assert fetched.id == created.id
    assert fetched.name == created.name

    updated = await store.organizations.update(
        created.id,
        models.Organization(**{**_organization().model_dump(), "name": "Renamed Organization"}),
    )
    assert updated.id == created.id
    assert updated.name == "Renamed Organization"

    assert [o.id for o in await store.organizations.list()] == [created.id]

    await store.organizations.delete(created.id)
    with pytest.raises(NotFoundError):
        await store.organizations.get(created.id)


async def test_get_missing_raises_not_found(store):
    with pytest.raises(NotFoundError):
        await store.organizations.get(-123)


async def test_delete_missing_raises_not_found(store):
    with pytest.raises(NotFoundError):
        await store.organizations.delete(-456)


async def test_location_rejects_dangling_organization_id(store):
    with pytest.raises(NotFoundError):
        await store.locations.create(_location(-789))


# ---- Registration engine ------------------------------------------------------


async def test_registration_respects_capacity_and_waitlists(store):
    opportunity = await _make_opportunity(store, capacity=1)
    first = await store.users.create(_user("first@example.org"))
    second = await store.users.create(_user("second@example.org"))

    approved = await store.participants.register(first.id, opportunity.id)
    waitlisted = await store.participants.register(second.id, opportunity.id)

    assert approved.approved is True
    assert waitlisted.approved is False


async def test_cancel_promotes_next_waitlisted_participant(store):
    opportunity = await _make_opportunity(store, capacity=1)
    first = await store.users.create(_user("first@example.org"))
    second = await store.users.create(_user("second@example.org"))

    approved = await store.participants.register(first.id, opportunity.id)
    waitlisted = await store.participants.register(second.id, opportunity.id)

    await store.participants.cancel(approved.id)

    promoted = await store.participants.get(waitlisted.id)
    assert promoted.approved is True


async def test_cancel_clears_approved_flag(store):
    opportunity = await _make_opportunity(store, capacity=5)
    user = await store.users.create(_user("cancel-approved@example.org"))
    participant = await store.participants.register(user.id, opportunity.id)
    assert participant.approved is True

    await store.participants.cancel(participant.id)

    cancelled = await store.participants.get(participant.id)
    assert cancelled.cancelled is True
    assert cancelled.approved is False


async def test_capacity_increase_promotes_waitlisted_participant(store):
    opportunity = await _make_opportunity(store, capacity=1)
    first = await store.users.create(_user("first@example.org"))
    second = await store.users.create(_user("second@example.org"))

    await store.participants.register(first.id, opportunity.id)
    waitlisted = await store.participants.register(second.id, opportunity.id)

    expanded = _opportunity(opportunity.location_id, opportunity.contact_id, capacity=2)
    await store.opportunities.update(opportunity.id, expanded)

    promoted = await store.participants.get(waitlisted.id)
    assert promoted.approved is True


async def test_duplicate_active_registration_conflicts(store):
    opportunity = await _make_opportunity(store, capacity=5)
    user = await store.users.create(_user("duplicate@example.org"))

    await store.participants.register(user.id, opportunity.id)
    with pytest.raises(ConflictError):
        await store.participants.register(user.id, opportunity.id)


async def test_reregistration_allowed_after_cancel(store):
    opportunity = await _make_opportunity(store, capacity=5)
    user = await store.users.create(_user("again@example.org"))

    first = await store.participants.register(user.id, opportunity.id)
    await store.participants.cancel(first.id)

    second = await store.participants.register(user.id, opportunity.id)
    assert second.id != first.id
    assert second.cancelled is False


async def test_cancel_is_idempotent(store):
    opportunity = await _make_opportunity(store, capacity=5)
    user = await store.users.create(_user("idempotent@example.org"))
    participant = await store.participants.register(user.id, opportunity.id)

    await store.participants.cancel(participant.id)
    await store.participants.cancel(participant.id)  # must not raise

    cancelled = await store.participants.get(participant.id)
    assert cancelled.cancelled is True


# ---- Empty string / NULL round-tripping (issue #15) --------------------------


async def test_organization_phone_optional(store):
    without_phone = _organization()
    without_phone.phone = None
    organization = await store.organizations.create(without_phone)
    assert organization.phone is None

    fetched = await store.organizations.get(organization.id)
    assert fetched.phone is None


async def test_opportunity_empty_notes_stored_as_null(store):
    opportunity = await _make_opportunity(store, capacity=1)
    assert opportunity.notes == ""

    fetched = await store.opportunities.get(opportunity.id)
    assert fetched.notes == ""

    if not isinstance(store, PostgresStore):
        return

    raw_notes = await store.pool.fetchval(
        "SELECT notes FROM opportunities WHERE id = $1;", opportunity.id
    )
    assert raw_notes is None
