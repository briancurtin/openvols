"""
Postgres Store implementation, via asyncpg.

* Schema lives in openvols.data.postgres.migrations (applied with yoyo, see yoyo.ini).
* Concurrency control for the registration engine relies on a single row lock per operation
  * See register()/cancel()/ _OpportunityRepository.update() for the transaction boundaries
  * This is used rather than an application-level advisory lock, since the opportunity row we need
    to lock is already the row we have to read for its capacity.
"""

import builtins
import typing

import asyncpg
import pydantic

from openvols import data, models


class _BasicRepository[StoredT: models.StoredModel, InputT: pydantic.BaseModel]:
    """
    Shared CRUD for tables whose columns match the Pydantic model's field names 1:1
    This includes organizations, users, locations, and agreements.

    Roles, opportunities, and participants each need more than a straight column
    mapping (an enum conversion, joins/validation, or registration-engine
    logic), so they're written out directly instead of forced through this.
    """

    def __init__(
        self, store: PostgresStore, table: str, columns: tuple[str, ...], stored_cls: type[StoredT]
    ):
        self._store = store
        self._table = table
        self._columns = columns
        self._stored_cls = stored_cls

    async def create(self, item: InputT) -> StoredT:
        """Insert an object and return its stored variant, which includes its id"""
        values = item.model_dump()
        placeholders = ", ".join(f"${i}" for i in range(1, len(self._columns) + 1))

        query = f"""
            INSERT INTO {self._table} ({", ".join(self._columns)})
            VALUES ({placeholders})
            RETURNING *;
            """

        row = await self._store.pool.fetchrow(query, *(values[column] for column in self._columns))

        assert row is not None

        return self._stored_cls(**dict(row))

    async def get(self, id: int) -> StoredT:
        """Given an id, return the stored object if it exists"""
        row = await self._store.pool.fetchrow(f"SELECT * FROM {self._table} WHERE id = $1;", id)

        if row is None:
            raise data.NotFoundError(self._stored_cls.__name__, id)

        return self._stored_cls(**dict(row))

    # `builtins.list`: see the comment on Repository.list in data/_store.py --
    # a bare `list` here would resolve to this method itself once Python 3.14
    # lazily evaluates the annotation.
    async def list(self) -> builtins.list[StoredT]:
        # TODO: The base implementation for right now is far too open. For repositories that are
        # per organization, which is all of them except Organizations itself, we will have to filter
        # based on that.
        rows = await self._store.pool.fetch(f"SELECT * FROM {self._table} ORDER BY created")

        return [self._stored_cls(**dict(row)) for row in rows]

    async def update(self, id: int, item: InputT) -> StoredT:
        values = item.model_dump()
        assignments = ", ".join(f"{column} = ${i + 1}" for i, column in enumerate(self._columns))

        query = f"""
            UPDATE {self._table} SET {assignments}
            WHERE id = ${len(self._columns) + 1}
            RETURNING *;
            """

        row = await self._store.pool.fetchrow(
            query, *(values[column] for column in self._columns), id
        )

        if row is None:
            raise data.NotFoundError(self._stored_cls.__name__, id)

        return self._stored_cls(**dict(row))

    async def delete(self, id: int) -> None:
        result = await self._store.pool.execute(f"DELETE FROM {self._table} WHERE id = $1;", id)

        if result == "DELETE 0":
            raise data.NotFoundError(self._stored_cls.__name__, id)


class _RoleRepository:
    """
    Plain CRUD for roles, plus validating that organization_id/user_id
    reference real records (the DB's own foreign keys are a backstop, not
    the primary mechanism -- see the module docstring's sibling note in
    openvols.data.memory for why: matching, precise NotFoundErrors across
    backends beats parsing a driver-specific constraint violation).
    """

    _COLUMNS = ("organization_id", "user_id", "type")

    def __init__(self, store: PostgresStore):
        self._store = store

    async def _validate(self, item: models.Role) -> None:
        # TODO: TaskGroup
        await self._store.organizations.get(item.organization_id)
        await self._store.users.get(item.user_id)

    async def create(self, item: models.Role) -> models.StoredRole:
        """Create a Role and return the StoredRole variant"""
        await self._validate(item)

        row = await self._store.pool.fetchrow(
            """INSERT INTO roles (organization_id, user_id, type)
               VALUES ($1, $2, $3)
               RETURNING *;
            """,
            item.organization_id,
            item.user_id,
            item.type.value,
        )

        assert row is not None

        return models.StoredRole(**dict(row))

    async def get(self, id: int) -> models.StoredRole:
        """Get a StoredRole from its id"""
        row = await self._store.pool.fetchrow("SELECT * FROM roles WHERE id = $1;", id)

        if row is None:
            raise data.NotFoundError("StoredRole", id)

        return models.StoredRole(**dict(row))

    async def list(self) -> builtins.list[models.StoredRole]:
        """Return the roles available"""
        # TODO: This should probably be filtered in all cases by user_id
        rows = await self._store.pool.fetch("SELECT * FROM roles ORDER BY created")
        return [models.StoredRole(**dict(row)) for row in rows]

    async def update(self, id: int, item: models.Role) -> models.StoredRole:
        await self._validate(item)

        row = await self._store.pool.fetchrow(
            """UPDATE roles
               SET organization_id = $1, user_id = $2, type = $3
               WHERE id = $4
               RETURNING *;
            """,
            item.organization_id,
            item.user_id,
            item.type.value,
            id,
        )

        if row is None:
            raise data.NotFoundError("StoredRole", id)

        return models.StoredRole(**dict(row))

    async def delete(self, id: int) -> None:
        """Delete a Role based on its id"""
        result = await self._store.pool.execute("DELETE FROM roles WHERE id = $1;", id)

        if result == "DELETE 0":
            raise data.NotFoundError("StoredRole", id)


class _LocationRepository:
    """Plain CRUD, plus validating that organization_id references a real Organization."""

    def __init__(self, store: PostgresStore):
        self._store = store
        self._repository = _BasicRepository(
            store,
            "locations",
            ("organization_id", "name", "address", "city", "state", "postal_code", "country"),
            models.StoredLocation,
        )

    async def create(self, item: models.Location) -> models.StoredLocation:
        """Create a Location

        This will only succeed if the Organization it references actually exists
        """
        await self._store.organizations.get(item.organization_id)
        return await self._repository.create(item)

    async def get(self, id: int) -> models.StoredLocation:
        """Get a Location by id"""
        return await self._repository.get(id)

    async def list(self) -> builtins.list[models.StoredLocation]:
        """List Locations"""
        # TODO: This may need to filter by organization
        # It may also make sense to eventually filter by geo above this
        return await self._repository.list()

    async def update(self, id: int, item: models.Location) -> models.StoredLocation:
        """Update a Location

        This will only succeed if the Organization it references actually exists
        """
        await self._store.organizations.get(item.organization_id)

        return await self._repository.update(id, item)

    async def delete(self, id: int) -> None:
        """Delete a Location by id"""
        await self._repository.delete(id)


class _AgreementRepository:
    """Plain CRUD, plus validating that organization_id references a real Organization."""

    def __init__(self, store: PostgresStore):
        self._store = store
        self._repository = _BasicRepository(
            store,
            "agreements",
            ("organization_id", "title", "description", "content", "valid", "invalid", "cadence"),
            models.StoredAgreement,
        )

    async def create(self, item: models.Agreement) -> models.StoredAgreement:
        """Create an Agreement

        Requires a valid organization_id in the Agreement object
        """
        await self._store.organizations.get(item.organization_id)

        return await self._repository.create(item)

    async def get(self, id: int) -> models.StoredAgreement:
        """Get an Agreement by id"""
        return await self._repository.get(id)

    async def list(self) -> builtins.list[models.StoredAgreement]:
        """List Agreements"""
        # TODO: This needs to be filtered by organization_id
        return await self._repository.list()

    async def update(self, id: int, item: models.Agreement) -> models.StoredAgreement:
        """Update an Agreement

        Requires a valid organization_id in the Agreement object
        """
        await self._store.organizations.get(item.organization_id)

        return await self._repository.update(id, item)

    async def delete(self, id: int) -> None:
        """Delete an Agreement by id"""
        await self._repository.delete(id)


_OPPORTUNITY_COLUMNS = (
    "title",
    "description",
    "location_id",
    "starts_at",
    "ends_at",
    "public",
    "open",
    "cancelled",
    "completed",
    "contact_id",
    "capacity",
    "notes",
    "auto_approve_registrants",
    "auto_approve_waiters",
)


def _opportunity_row_values(item: models.Opportunity) -> dict[str, object]:
    """Map Opportunity's start/end fields onto the starts_at/ends_at columns."""
    values = item.model_dump()
    values["starts_at"] = values.pop("start")
    values["ends_at"] = values.pop("end")

    del values["agreement_ids"]

    return values


def _opportunity_from_row(
    row: asyncpg.Record, agreement_ids: list[int]
) -> models.StoredOpportunity:
    """Convert a Postgres record into a StoredOpportunity"""
    values = dict(row)
    values["start"] = values.pop("starts_at")
    values["end"] = values.pop("ends_at")

    return models.StoredOpportunity(agreement_ids=agreement_ids, **values)


class _OpportunityRepository:
    """
    CRUD, plus validation of location_id/contact_id/agreement_ids

    This implementation triggers waitlist promotion on update().
    See _ParticipantRepository.register/cancel for another promotion.
    """

    def __init__(self, store: PostgresStore, participants: _ParticipantRepository):
        self._store = store
        # Held as the concrete type (not reached via self._store.participants,
        # which is typed as the public data.ParticipantRepository protocol)
        # because update() below needs _promote_waitlist(), deliberately left
        # off that protocol -- see _ParticipantRepository's docstring.
        self._participants = participants

    async def _validate(self, item: models.Opportunity) -> None:
        """Validate that any nested/referenced objects within an Opportunity exist"""
        # TODO: Run these queries concurrently. None of them reference incrementally available
        # data, and they can all safely be requested concurrently.
        await self._store.locations.get(item.location_id)
        await self._store.users.get(item.contact_id)
        for agreement_id in item.agreement_ids:
            await self._store.agreements.get(agreement_id)

    async def _agreement_ids(
        self, conn: asyncpg.pool.PoolConnectionProxy, id: int
    ) -> builtins.list[int]:
        """Get the agreements for a single opportunity"""
        rows = await conn.fetch(
            """SELECT agreement_id
               FROM opportunity_agreements WHERE opportunity_id = $1
               ORDER BY agreement_id
            """,
            id,
        )

        return [row["agreement_id"] for row in rows]

    async def create(self, item: models.Opportunity) -> models.StoredOpportunity:
        """Create an Opportunity and returned its stored variant

        Requires valid location_id, contact_id, and agreement_ids
        """
        await self._validate(item)

        values = _opportunity_row_values(item)
        placeholders = ", ".join(f"${i}" for i in range(1, len(_OPPORTUNITY_COLUMNS) + 1))

        async with self._store.pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                f"""INSERT INTO opportunities ({", ".join(_OPPORTUNITY_COLUMNS)})
                    VALUES ({placeholders})
                    RETURNING *;""",
                *(values[column] for column in _OPPORTUNITY_COLUMNS),
            )

            for agreement_id in item.agreement_ids:
                await conn.execute(
                    """INSERT INTO opportunity_agreements (opportunity_id, agreement_id)
                       VALUES ($1, $2);
                    """,
                    row["id"],
                    agreement_id,
                )

        assert row is not None

        return _opportunity_from_row(row, list(item.agreement_ids))

    async def get(self, id: int) -> models.StoredOpportunity:
        """Get an Opportunity by id"""
        async with self._store.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM opportunities WHERE id = $1;", id)

            if row is None:
                raise data.NotFoundError("StoredOpportunity", id)

            agreement_ids = await self._agreement_ids(conn, id)

        return _opportunity_from_row(row, agreement_ids)

    async def list(self) -> builtins.list[models.StoredOpportunity]:
        """List Opportunities"""
        # TODO: This should be filtered at least by organization_id, eventually
        # by geo details but probably from a higher level
        async with self._store.pool.acquire() as conn:
            # TODO: This should probably sort by start, not created...
            rows = await conn.fetch("SELECT * FROM opportunities ORDER BY created;")

            # TODO
            # 1. I don't like how this gets formatted. List comprehensions are great one-liners.
            # 2. This will read and probably work better if we support getting agreements
            #    from multiple opportunities instead of looping here. Push this into a single query.
            return [
                _opportunity_from_row(row, await self._agreement_ids(conn, row["id"]))
                for row in rows
            ]

    async def update(self, id: int, item: models.Opportunity) -> models.StoredOpportunity:
        """Update an Opportunity

        Requires valid location_id, contact_id, and agreement_ids
        """
        await self._validate(item)

        values = _opportunity_row_values(item)
        assignments = ", ".join(
            f"{column} = ${i + 1}" for i, column in enumerate(_OPPORTUNITY_COLUMNS)
        )
        async with self._store.pool.acquire() as conn, conn.transaction():
            # Locks the opportunity row for the rest of this transaction --
            # see the module docstring. UPDATE itself already takes this
            # lock, so a separate SELECT ... FOR UPDATE isn't needed here.
            row = await conn.fetchrow(
                f"""UPDATE opportunities
                    SET {assignments}
                    WHERE id = ${len(_OPPORTUNITY_COLUMNS) + 1}
                    RETURNING *;
                """,
                *(values[column] for column in _OPPORTUNITY_COLUMNS),
                id,
            )

            if row is None:
                raise data.NotFoundError("StoredOpportunity", id)

            # The following could be short-circuited by checking if there was any change
            # to agreements, but I expect it's not an often used action and should have
            # limited overhead. This is perfectly functional without the added special case
            # so let's prefer it until we can't.
            # If this becomes costly, technically we could use something based
            # on `RETURNING OLD` or `OLD IS DISTINCT FROM NEW` and skip the delete
            # and only need to insert new agreements while leaving old ones alone.
            #
            # TODO: Do we need ON DELETE CASCADE anywhere to ensure there aren't orphans here?
            await conn.execute("DELETE FROM opportunity_agreements WHERE opportunity_id = $1;", id)

            for agreement_id in item.agreement_ids:
                await conn.execute(
                    """INSERT INTO opportunity_agreements (opportunity_id, agreement_id)
                       VALUES ($1, $2);
                    """,
                    id,
                    agreement_id,
                )

            await self._participants._promote_waitlist(conn, id)

        return _opportunity_from_row(row, list(item.agreement_ids))

    async def delete(self, id: int) -> None:
        """Delete an Opportunity"""
        # TODO: Do we ever want this to be a "soft" delete instead?
        result = await self._store.pool.execute("DELETE FROM opportunities WHERE id = $1;", id)

        if result == "DELETE 0":
            raise data.NotFoundError("StoredOpportunity", id)


class _ParticipantRepository:
    """
    The registration engine

    Every mutating method here, plus _OpportunityRepository.update(),
    locks the opportunity row via `SELECT ... FOR UPDATE` before reading
    or writing any of its participants. Because that's the *only* lock ever taken,
    and it's always the same single row per transaction, there's no lock-ordering
    deadlock to worry about; holding it is what makes the capacity reads and FIFO
    promotion below safe under concurrent registrations.
    """

    def __init__(self, store: PostgresStore):
        self._store = store

    @staticmethod
    def _from_row(row: asyncpg.Record) -> models.StoredParticipant:
        return models.StoredParticipant(**dict(row))

    async def get(self, id: int) -> models.StoredParticipant:
        """Get a Participant"""
        row = await self._store.pool.fetchrow("""SELECT * FROM participants WHERE id = $1;""", id)

        if row is None:
            raise data.NotFoundError("StoredParticipant", id)

        return self._from_row(row)

    async def list(self) -> builtins.list[models.StoredParticipant]:
        """List Particpants"""
        # TODO: This needs to be filtered by opportunity_id. It doesn't make sense otherwise.
        rows = await self._store.pool.fetch("SELECT * FROM participants ORDER BY created")

        return [self._from_row(row) for row in rows]

    async def update(self, id: int, item: models.Participant) -> models.StoredParticipant:
        """Update a Participant"""
        # TODO: Can we loosen updates from the schema? We can't just pass `approved=true`
        # here, which need the fully formed object. From the API layer it would be nicer to
        # only need to pass through updates since we're using PATCH up there.
        row = await self._store.pool.fetchrow(
            """UPDATE participants
               SET user_id = $1, opportunity_id = $2, approved = $3,
                   cancelled = $4, attended = $5
               WHERE id = $6
               RETURNING *;
            """,
            item.user_id,
            item.opportunity_id,
            item.approved,
            item.cancelled,
            item.attended,
            id,
        )

        if row is None:
            raise data.NotFoundError("StoredParticipant", id)

        return self._from_row(row)

    async def delete(self, id: int) -> None:
        """Delete a Participant by id"""
        result = await self._store.pool.execute("DELETE FROM participants WHERE id = $1", id)

        if result == "DELETE 0":
            raise data.NotFoundError("StoredParticipant", id)

    async def register(self, user_id: int, opportunity_id: int) -> models.StoredParticipant:
        """Register a User as a Participant on an Opportunity"""
        await self._store.users.get(user_id)

        async with self._store.pool.acquire() as conn, conn.transaction():
            # Lock the opportunity via FOR UPDATE while we have
            # the current capacity in order to decide whether or not this
            # participant is going to be waitlisted or registered straight away.
            opportunity = await conn.fetchrow(
                """SELECT capacity
                   FROM opportunities
                   WHERE id = $1
                    FOR UPDATE;
                """,
                opportunity_id,
            )
            if opportunity is None:
                raise data.NotFoundError("StoredOpportunity", opportunity_id)

            active = await conn.fetchval(
                """SELECT count(*)
                   FROM participants
                   WHERE user_id = $1
                         AND opportunity_id = $2
                         AND NOT cancelled;
                """,
                user_id,
                opportunity_id,
            )

            if active:
                raise data.ConflictError(
                    f"user {user_id!r} is already registered for opportunity {opportunity_id!r}"
                )

            # BUG: We locked the opportunity to determine its total capacity
            # but `participants` is the capcaity that matters for approval.
            # At no point in here is `participants` a consistent target.
            # 1. We could get that the user is inactive on L555 and another request
            #    could be inserting/updating them.
            # 2. We could get that two users are inactive in concurrent requests
            #    with only one capacity slot but both could get it in L590.

            approved_count = await conn.fetchval(
                """SELECT count(*)
                   FROM participants
                   WHERE opportunity_id = $1
                         AND approved
                         AND NOT cancelled;
                """,
                opportunity_id,
            )

            row = await conn.fetchrow(
                """INSERT INTO participants
                          (user_id, opportunity_id, approved, cancelled, attended)
                   VALUES ($1, $2, $3, FALSE, FALSE)
                   RETURNING *;""",
                user_id,
                opportunity_id,
                approved_count < opportunity["capacity"],
            )

        assert row is not None

        return self._from_row(row)

    async def cancel(self, participant_id: int) -> None:
        # opportunity_id is immutable once a participant is created, so
        # reading it doesn't need to happen inside the locked section below.
        opportunity_id = await self._store.pool.fetchval(
            """SELECT opportunity_id
               FROM participants
               WHERE id = $1;
            """,
            participant_id,
        )

        if opportunity_id is None:
            raise data.NotFoundError("StoredParticipant", participant_id)

        async with self._store.pool.acquire() as conn, conn.transaction():
            await conn.execute(
                """SELECT id
                   FROM opportunities
                   WHERE id = $1
                    FOR UPDATE;""",
                opportunity_id,
            )

            # BUG: Similar to inside of register, participant count is what
            # could move. The opportunity row being locked is not enough.
            participant = await conn.fetchrow(
                """SELECT approved, cancelled
                   FROM participants
                   WHERE id = $1;
                """,
                participant_id,
            )

            if participant is None or participant["cancelled"]:
                return

            await conn.execute(
                """UPDATE participants
                   SET cancelled = TRUE
                   WHERE id = $1;
                """,
                participant_id,
            )

            if participant["approved"]:
                await self._promote_waitlist(conn, opportunity_id)

    async def _promote_waitlist(
        self, conn: asyncpg.pool.PoolConnectionProxy, opportunity_id: int
    ) -> None:
        """
        Approve waitlisted participants FIFO until capacity is filled.
        Assumes the caller already holds the opportunity's row lock for the
        current transaction -- see the class docstring.
        """
        capacity = await conn.fetchval(
            """SELECT capacity
               FROM opportunities
               WHERE id = $1;
            """,
            opportunity_id,
        )
        approved_count = await conn.fetchval(
            """SELECT count(*)
               FROM participants
               WHERE opportunity_id = $1
                     AND approved
                     AND NOT cancelled;
            """,
            opportunity_id,
        )

        open_slots = capacity - approved_count
        if open_slots <= 0:
            return

        await conn.execute(
            """UPDATE participants
               SET approved = TRUE
               WHERE id IN (
                    SELECT id FROM participants
                    WHERE opportunity_id = $1 AND NOT
                          approved AND NOT
                          cancelled
                    ORDER BY created ASC LIMIT $2
               );
            """,
            opportunity_id,
            open_slots,
        )


class PostgresStore:
    """Postgres Store: every repository shares one asyncpg connection pool."""

    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None
        self.organizations: data.OrganizationRepository = _BasicRepository(
            self,
            "organizations",
            (
                "name",
                "description",
                "website",
                "contact",
                "email",
                "phone",
                "private_allowed",
                "approved",
            ),
            models.StoredOrganization,
        )
        self.users: data.UserRepository = _BasicRepository(
            self,
            "users",
            (
                "first_name",
                "last_name",
                "email",
                "email_reminders",
                "phone",
                "phone_reminders",
            ),
            models.StoredUser,
        )
        self.roles: data.RoleRepository = _RoleRepository(self)
        self.locations: data.LocationRepository = _LocationRepository(self)
        self.agreements: data.AgreementRepository = _AgreementRepository(self)
        self.participants: data.ParticipantRepository = _ParticipantRepository(self)
        self.opportunities: data.OpportunityRepository = _OpportunityRepository(
            self, self.participants
        )

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("PostgresStore used before entering its async context")
        return self._pool

    async def __aenter__(self) -> typing.Self:
        self._pool = await asyncpg.create_pool(self._dsn)
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
