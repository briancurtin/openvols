"""
Boundary and property-based coverage for the field constraints and
model_validators on User/Agreement/Opportunity/Participant (see
openvols.models). Pure model construction -- no store or API involved.

Hypothesis is used for the genuinely range-based/infinite-domain properties
(lengths, date orderings, capacity); finite state spaces (Participant's three
booleans) are also driven through Hypothesis since it exhaustively covers a
space that small, but the assertion is written as a plain invariant rather
than a table of expected combinations.
"""

from datetime import UTC, datetime, timedelta

import pydantic
import pytest
from hypothesis import given
from hypothesis import strategies as st

from openvols import models

# ---- helpers: valid kwargs for each model, so each test overrides only the
# field(s) it's exercising -----------------------------------------------------


def _user_kwargs(**overrides) -> dict:
    kwargs = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.org",
        "email_reminders": True,
        "phone": "+12025550182",
        "phone_reminders": True,
    }
    kwargs.update(overrides)
    return kwargs


def _organization_kwargs(**overrides) -> dict:
    kwargs = {
        "name": "Example Organization",
        "description": "A volunteer organization",
        "website": "https://example.org",
        "contact": "jane@example.org",
        "email": "contact@example.org",
        "phone": "+12025550182",
        "private_allowed": False,
        "approved": True,
    }
    kwargs.update(overrides)
    return kwargs


def _agreement_kwargs(**overrides) -> dict:
    kwargs = {
        "organization_id": 1,
        "title": "Volunteer Waiver",
        "description": "Standard liability waiver",
        "content": "By participating in this opportunity you agree to the terms outlined here.",
        "valid": datetime(2026, 1, 1, tzinfo=UTC),
        "invalid": datetime(2027, 1, 1, tzinfo=UTC),
        "cadence": models.AgreementCadence.PER_OPPORTUNITY,
    }
    kwargs.update(overrides)
    return kwargs


def _location_kwargs(**overrides) -> dict:
    kwargs = {
        "organization_id": 1,
        "name": "Community Center",
        "address": "123 Main St",
        "city": "Springfield",
        "state": "IL",
        "postal_code": "62701",
        "country": "US",
    }
    kwargs.update(overrides)
    return kwargs


def _opportunity_kwargs(**overrides) -> dict:
    kwargs = {
        "title": "Park Cleanup Day",
        "description": (
            "Join volunteers for a community cleanup at the park: picking up litter, "
            "weeding garden beds, repainting benches, and clearing walking trails."
        ),
        "location_id": 1,
        "start": datetime(2026, 6, 1, 9, tzinfo=UTC),
        "end": datetime(2026, 6, 1, 12, tzinfo=UTC),
        "public": True,
        "open": True,
        "cancelled": False,
        "completed": False,
        "contact_id": 1,
        "capacity": 10,
        "notes": "",
        "auto_approve_registrants": True,
        "auto_approve_waiters": True,
    }
    kwargs.update(overrides)
    return kwargs


def _participant_kwargs(**overrides) -> dict:
    kwargs = {
        "user_id": 1,
        "opportunity_id": 1,
        "approved": False,
        "cancelled": False,
        "attended": False,
    }
    kwargs.update(overrides)
    return kwargs


# ---- User ---------------------------------------------------------------------


def test_phone_reminders_requires_phone():
    with pytest.raises(pydantic.ValidationError):
        models.User(**_user_kwargs(phone=None, phone_reminders=True))


def test_phone_reminders_false_allows_missing_phone():
    user = models.User(**_user_kwargs(phone=None, phone_reminders=False))
    assert user.phone is None


@given(phone_reminders=st.booleans())
def test_phone_reminders_with_valid_phone_always_succeeds(phone_reminders):
    user = models.User(**_user_kwargs(phone="+12025550182", phone_reminders=phone_reminders))
    assert user.phone_reminders is phone_reminders


# Location


def test_location_name_min():
    with pytest.raises(pydantic.ValidationError):
        models.Location(**_location_kwargs(name="no"))


def test_location_address_min():
    with pytest.raises(pydantic.ValidationError):
        models.Location(**_location_kwargs(address="no"))


def test_location_city_min():
    with pytest.raises(pydantic.ValidationError):
        models.Location(**_location_kwargs(city="no"))


def test_location_state_invalid_value():
    with pytest.raises(pydantic.ValidationError):
        models.Location(**_location_kwargs(state="XX"))


@pytest.mark.parametrize("length", [0, 1, 3, 4, 5])
def test_location_state_wrong_length(length):
    with pytest.raises(pydantic.ValidationError):
        models.Location(**_location_kwargs(state="X" * length))


@pytest.mark.parametrize("country", ["us", "usa", "Us", "USA"])
def test_location_country_convert(country):
    location = models.Location(**_location_kwargs(country=country))
    assert location.country == "US"


# ---- Organization ---------------------------------------------------------------


def test_organization_phone_optional():
    organization = models.Organization(**_organization_kwargs(phone=None))
    assert organization.phone is None


def test_organization_website_improper_format():
    with pytest.raises(pydantic.ValidationError):
        models.Organization(**_organization_kwargs(website="website.com"))


def test_organization_website_omitted_default():
    # The website column is now nullable
    kwargs = _organization_kwargs()
    kwargs.pop("website")

    organization = models.Organization(**kwargs)
    assert organization.website == None


# ---- Agreement ------------------------------------------------------------------


@given(delta=st.timedeltas(min_value=timedelta(seconds=1), max_value=timedelta(days=3650)))
def test_agreement_invalid_after_valid_accepted(delta):
    valid = datetime(2026, 1, 1, tzinfo=UTC)
    agreement = models.Agreement(**_agreement_kwargs(valid=valid, invalid=valid + delta))
    assert agreement.invalid > agreement.valid


@given(delta=st.timedeltas(min_value=timedelta(0), max_value=timedelta(days=3650)))
def test_agreement_invalid_before_or_equal_valid_rejected(delta):
    valid = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(pydantic.ValidationError):
        models.Agreement(**_agreement_kwargs(valid=valid, invalid=valid - delta))


@given(length=st.integers(min_value=0, max_value=9))
def test_agreement_title_too_short_rejected(length):
    with pytest.raises(pydantic.ValidationError):
        models.Agreement(**_agreement_kwargs(title="x" * length))


@given(length=st.integers(min_value=10, max_value=80))
def test_agreement_title_min_length_accepted(length):
    agreement = models.Agreement(**_agreement_kwargs(title="x" * length))
    assert len(agreement.title) == length


@given(length=st.integers(min_value=81, max_value=200))
def test_agreement_title_too_long_rejected(length):
    with pytest.raises(pydantic.ValidationError):
        models.Agreement(**_agreement_kwargs(title="x" * length))


# ---- Opportunity ------------------------------------------------------------------


@given(delta=st.timedeltas(min_value=timedelta(seconds=1), max_value=timedelta(days=3650)))
def test_opportunity_end_after_start_accepted(delta):
    start = datetime(2026, 6, 1, tzinfo=UTC)
    opportunity = models.Opportunity(**_opportunity_kwargs(start=start, end=start + delta))
    assert opportunity.end > opportunity.start


@given(delta=st.timedeltas(min_value=timedelta(0), max_value=timedelta(days=3650)))
def test_opportunity_end_before_or_equal_start_rejected(delta):
    start = datetime(2026, 6, 1, tzinfo=UTC)
    with pytest.raises(pydantic.ValidationError):
        models.Opportunity(**_opportunity_kwargs(start=start, end=start - delta))


@given(capacity=st.integers(min_value=0, max_value=10_000))
def test_opportunity_non_negative_capacity_accepted(capacity):
    opportunity = models.Opportunity(**_opportunity_kwargs(capacity=capacity))
    assert opportunity.capacity == capacity


@given(capacity=st.integers(min_value=-10_000, max_value=-1))
def test_opportunity_negative_capacity_rejected(capacity):
    with pytest.raises(pydantic.ValidationError):
        models.Opportunity(**_opportunity_kwargs(capacity=capacity))


@given(length=st.integers(min_value=0, max_value=9))
def test_opportunity_title_too_short_rejected(length):
    with pytest.raises(pydantic.ValidationError):
        models.Opportunity(**_opportunity_kwargs(title="x" * length))


@given(length=st.integers(min_value=10, max_value=200))
def test_opportunity_title_min_length_accepted(length):
    opportunity = models.Opportunity(**_opportunity_kwargs(title="x" * length))
    assert len(opportunity.title) == length


@given(length=st.integers(min_value=0, max_value=99))
def test_opportunity_description_too_short_rejected(length):
    with pytest.raises(pydantic.ValidationError):
        models.Opportunity(**_opportunity_kwargs(description="x" * length))


@given(length=st.integers(min_value=100, max_value=1000))
def test_opportunity_description_min_length_accepted(length):
    opportunity = models.Opportunity(**_opportunity_kwargs(description="x" * length))
    assert len(opportunity.description) == length


def test_completed_before_end_rejected():
    future = datetime.now(UTC) + timedelta(days=365)
    with pytest.raises(pydantic.ValidationError):
        models.Opportunity(
            **_opportunity_kwargs(start=future, end=future + timedelta(hours=3), completed=True)
        )


def test_completed_after_end_accepted():
    past_start = datetime.now(UTC) - timedelta(days=2)
    past_end = datetime.now(UTC) - timedelta(days=1)
    opportunity = models.Opportunity(
        **_opportunity_kwargs(start=past_start, end=past_end, completed=True)
    )
    assert opportunity.completed is True


@given(offset=st.timedeltas(min_value=timedelta(days=1), max_value=timedelta(days=3650)))
def test_completed_requires_end_in_the_past(offset):
    now = datetime.now(UTC)
    with pytest.raises(pydantic.ValidationError):
        models.Opportunity(
            **_opportunity_kwargs(
                start=now + offset, end=now + offset + timedelta(hours=1), completed=True
            )
        )


def test_opportunity_notes_omitted_default():
    kwargs = _opportunity_kwargs()
    kwargs.pop("notes")

    opp = models.Opportunity(**kwargs)
    assert opp.notes == ""


# ---- Participant ------------------------------------------------------------------


@given(approved=st.booleans(), cancelled=st.booleans(), attended=st.booleans())
def test_participant_state_matches_invariant(approved, cancelled, attended):
    valid = not (cancelled and (approved or attended))
    kwargs = _participant_kwargs(approved=approved, cancelled=cancelled, attended=attended)

    if valid:
        participant = models.Participant(**kwargs)
        assert participant.cancelled == cancelled
    else:
        with pytest.raises(pydantic.ValidationError):
            models.Participant(**kwargs)
