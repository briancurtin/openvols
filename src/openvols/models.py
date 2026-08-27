"""
Base models for the OpenVols system

These represent the most detailed view of the objects from the lowest level
and are what the data store works with. Higher levels, such as inputs and outputs
in the HTTP layer will be subsets of these.
"""

import enum
import typing
from datetime import UTC, datetime

import pydantic
from pydantic_extra_types.phone_numbers import PhoneNumber


class USPhoneNumber(PhoneNumber):
    """
    Limit supported phone numbers to US-only for now

    NOTE: This will convert '123-456-7890' to '(123) 456-7890' during creation

    This was taken verbatim from the PhoneNumber documentation
    """

    default_region_code = "US"
    # pydantic knows how to work with mutable default arguments
    supported_regions = ["US"]  # noqa: RUF012
    phone_format = "NATIONAL"


class StoredModel(pydantic.BaseModel):
    """An object that exists in the database"""

    id: int
    created: datetime | None = None
    updated: datetime | None = None


class Organization(pydantic.BaseModel):
    """An organization to create. Requires approval."""

    name: str = pydantic.Field(min_length=3)  # Could be a three-letter acronym
    description: str = pydantic.Field(min_length=20)
    website: str  # Possible to not have a website, I guess
    contact: pydantic.EmailStr
    email: pydantic.EmailStr
    phone: USPhoneNumber | None = None
    private_allowed: bool
    approved: bool


class StoredOrganization(StoredModel, Organization):
    """An Organization in the data layer"""


class User(pydantic.BaseModel):
    """
    A User is a person with an email address who participates in Opportunities

    Users by default have no role, and one can be assumed if the role is granted
    on a per-organization basis. For example, a user may be a volunteer for one
    organization and a manager for another.
    """

    # This may have to be tested in the real world to see how it works out,
    # but some people may just want to sign up with initials. That may not
    # work with agreements, which could be binding, so there may need to be
    # some more strict requirement here on names, and over there on accepting
    # initials. TBD.
    first_name: str = pydantic.Field(min_length=1)
    last_name: str = pydantic.Field(min_length=1)
    email: pydantic.EmailStr
    email_reminders: bool
    phone: USPhoneNumber | None = None
    phone_reminders: bool

    @pydantic.model_validator(mode="after")
    def _phone_reminders_require_phone(self) -> typing.Self:
        if self.phone_reminders and self.phone is None:
            raise ValueError("phone_reminders requires a phone number")
        return self


class StoredUser(StoredModel, User):
    """A User in the data layer"""


class RoleType(enum.Enum):
    """A RoleType is a the level permission granted to a User for an Organization."""

    USER = 0
    MANAGER = 1
    ADMIN = 2
    SUPER_ADMIN = 99


class Role(pydantic.BaseModel):
    """
    A User may have a role for a given Organization

    Users default to having no role and can assume elevated permissions within an Organization
    if a role is granted for one.

    * Super Admins have access to the entire platform
    * Admins have access to all data for an Organization and can elevate users to managers,
      and manage the Organization and its Opportunities and their related objects.
    * Managers can manage Opportunities and Participants.
    """

    organization_id: int
    user_id: int
    type: RoleType


class StoredRole(StoredModel, Role):
    """A Role in the data layer"""


# fmt: off
_US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "PR",  # Puerto Rico should be a state
}
# fmt: on


class Location(pydantic.BaseModel):
    """
    A Location is the place where an Opportunity will take place

    Currently only supports US addresses with:
    * two-letter state
    * five digit zip code
    * hardcoded to US
    """

    organization_id: int
    name: str = pydantic.Field(min_length=4)  # Could be "main"
    address: str = pydantic.Field(min_length=9)  # "1 main st" is the min
    city: str = pydantic.Field(min_length=3)
    state: str = pydantic.Field(min_length=2, max_length=2)
    postal_code: str = pydantic.Field(min_length=5, max_length=5)
    country: str = pydantic.Field(min_length=2, max_length=3)

    @pydantic.field_validator("state")
    def _validate_state(cls, value: str) -> str:
        val = value.upper()
        if val not in _US_STATES:
            raise ValueError(f"{val} is not a US state")

        return val

    @pydantic.field_validator("postal_code")
    def _validate_postal_code(cls, value: str) -> str:
        """
        postal_code is named to be international friendly but is strictly
        for US zip codes right now. As such, it will be input as a string
        and stored as a string, but we check that it would evaluate to an int
        because US zip codes are numbers (with leading zeroes), and we want
        to ensure we're storing something that could be a reasonable zip
        instead of something like 'asdfg'.
        """
        try:
            int(value)
        except TypeError:
            raise ValueError(f"{val} is not a US state")

        return value

    @pydantic.field_validator("country")
    def _validate_country(cls, value: str) -> str:
        """Coerce all forms of US or USA to US, and reject other countries"""

        if value.upper() not in ("US", "USA"):
            raise ValueError("This platform currently only supports US addresses")

        return "US"


class StoredLocation(StoredModel, Location):
    """A Location in the data layer"""


class AgreementCadence(enum.StrEnum):
    """
    An AgreementCadence represents how often an agreement needs to be accepted.

    - Perpetual agreements are accepted once and do not expire.
    - Annual agreements must be accepted once per calendar year.
    - Per Opportunity agreements must be accepted per opportunity.
    """

    PER_OPPORTUNITY = "per_opportunity"
    ANNUAL = "annual"
    PERPETUAL = "perpetual"


class Agreement(pydantic.BaseModel):
    """
    An Agreement is a document that a User must accept in order to participate in an Opportunity.

    Agreements are immutable, and the Organization is responsibile for its content.
    An Agreement considered valid from the `valid` date until set at its creation until
    it's marked as `invalid` by an Organization admin.

    Instead of editing an Agreement, invalidate it and create a new one. This ensures no agreements
    are modified after a user has accepted them, preserving history of the state at acceptance.
    """

    organization_id: int
    title: str = pydantic.Field(min_length=10, max_length=80)
    # Description is intended to be a sub-title, a sentence or two summary.
    description: str = pydantic.Field(min_length=10, max_length=120)
    content: str = pydantic.Field(min_length=50)
    valid: datetime
    invalid: datetime
    cadence: AgreementCadence

    @pydantic.model_validator(mode="after")
    def _invalid_after_valid(self) -> typing.Self:
        if self.invalid <= self.valid:
            raise ValueError("invalid must be after valid")
        return self


class StoredAgreement(StoredModel, Agreement):
    """An Agreement in the data layer"""


class Opportunity(pydantic.BaseModel):
    """
    An Opportunity is an event at a location at a set time that users can participate in.

    * `title` is a quick name of the opportunity, which shows up on a list of opportunities
    * `description` is a longer explanation of the opportunity
    * `start` and `end` are the times the opportunity is open for participation
    * `location_id` is the place where the opportunity takes place
    * `public` indicates whether the opportunity is visible to all users or only to those
      with a link
    * `cancelled` indicates whether the opportunity has been cancelled and is no longer available
      for participation
    * `completed` indicates whether the opportunity's date has passed and the event took place
    * `contact_id` is the user who is responsible for the opportunity and can be contacted
      for questions
    * `capacity` is the maximum number of participants allowed for the opportunity.
      Users that register for the opportunity will be added as participants but with
      `approved=False` unless and until an Organization manager approves them.
    * `auto_approve_registrants` indicates whether users that register for the opportunity
      are automatically approved as participants when there is sufficient capacity,
      or if they require approval by an Organization manager.
    * `auto_approve_waiters` indicates whether users that are not approved as participants
      can be automatically promoted upon cancellation of another participant or expansion of
      the opportunity's capacity, or if they require approval by an Organization manager.
    * `agreement_ids` are the agreements that users must accept in order to participate
      in the opportunity. Each agreement specifies its own acceptance cadence.
    """

    title: str = pydantic.Field(min_length=10)
    description: str = pydantic.Field(min_length=100)
    location_id: int
    start: datetime
    end: datetime
    public: bool
    open: bool
    cancelled: bool
    completed: bool
    contact_id: int
    capacity: int = pydantic.Field(ge=0)
    notes: str
    auto_approve_registrants: bool
    auto_approve_waiters: bool
    agreement_ids: list[int] = pydantic.Field(default_factory=list)

    @pydantic.model_validator(mode="after")
    def _end_after_start(self) -> typing.Self:
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self

    @pydantic.model_validator(mode="after")
    def _completed_requires_end_passed(self) -> typing.Self:
        if self.completed and datetime.now(UTC) <= self.end:
            raise ValueError("completed can't be True before end has passed")
        return self


class StoredOpportunity(StoredModel, Opportunity):
    """An Opportunity in the data layer"""


class Participant(pydantic.BaseModel):
    """
    A Participant is a User who has registered for an Opportunity.

    * `approved` participants were either auto-approved by the registration engine,
      or were manually approved by an Organization manager.
    * `cancelled` is generally set by the user, changing their intent to participate.
      Updates to `cancelled` trigger registration to see if any approved=false users
      should be approved to fill the opportunity's capacity.
    * `attended` tracks whether or not the participant actually attended the opportunity.
    """

    user_id: int
    opportunity_id: int
    approved: bool
    cancelled: bool
    attended: bool

    @pydantic.model_validator(mode="after")
    def _cancelled_excludes_approved_and_attended(self) -> typing.Self:
        if self.cancelled and self.approved:
            raise ValueError("a participant can't be both approved and cancelled")
        if self.cancelled and self.attended:
            raise ValueError("a participant can't be both attended and cancelled")
        return self


class StoredParticipant(StoredModel, Participant):
    """A Participant in the data layer"""
