-- Initial schema for the Postgres Store backend.
--
-- ids/created/updated are set by application code (see
-- openvols.data.postgres._store), not database defaults, so every backend
-- generates them the same way.

CREATE TABLE organizations (
    id TEXT PRIMARY KEY,
    created TIMESTAMPTZ NOT NULL,
    updated TIMESTAMPTZ NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    website TEXT NOT NULL,
    contact TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    private_allowed BOOLEAN NOT NULL,
    approved BOOLEAN NOT NULL
);

CREATE TABLE users (
    id TEXT PRIMARY KEY,
    created TIMESTAMPTZ NOT NULL,
    updated TIMESTAMPTZ NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    email_reminders BOOLEAN NOT NULL,
    phone TEXT NOT NULL,
    phone_reminders BOOLEAN NOT NULL
);

CREATE TABLE roles (
    id TEXT PRIMARY KEY,
    created TIMESTAMPTZ NOT NULL,
    updated TIMESTAMPTZ NOT NULL,
    organization_id TEXT NOT NULL REFERENCES organizations (id),
    user_id TEXT NOT NULL REFERENCES users (id),
    type SMALLINT NOT NULL
);

CREATE TABLE locations (
    id TEXT PRIMARY KEY,
    created TIMESTAMPTZ NOT NULL,
    updated TIMESTAMPTZ NOT NULL,
    organization_id TEXT NOT NULL REFERENCES organizations (id),
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    country TEXT NOT NULL
);

CREATE TABLE agreements (
    id TEXT PRIMARY KEY,
    created TIMESTAMPTZ NOT NULL,
    updated TIMESTAMPTZ NOT NULL,
    organization_id TEXT NOT NULL REFERENCES organizations (id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    content TEXT NOT NULL,
    valid TIMESTAMPTZ NOT NULL,
    invalid TIMESTAMPTZ NOT NULL,
    cadence TEXT NOT NULL
);

-- start/end are reserved words, so the columns are named to avoid quoting
-- every reference to them throughout the query layer.
CREATE TABLE opportunities (
    id TEXT PRIMARY KEY,
    created TIMESTAMPTZ NOT NULL,
    updated TIMESTAMPTZ NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    location_id TEXT NOT NULL REFERENCES locations (id),
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    public BOOLEAN NOT NULL,
    open BOOLEAN NOT NULL,
    cancelled BOOLEAN NOT NULL,
    completed BOOLEAN NOT NULL,
    contact_id TEXT NOT NULL REFERENCES users (id),
    capacity INTEGER NOT NULL CHECK (capacity >= 0),
    notes TEXT NOT NULL,
    auto_approve_registrants BOOLEAN NOT NULL,
    auto_approve_waiters BOOLEAN NOT NULL
);

CREATE TABLE opportunity_agreements (
    opportunity_id TEXT NOT NULL REFERENCES opportunities (id),
    agreement_id TEXT NOT NULL REFERENCES agreements (id),
    PRIMARY KEY (opportunity_id, agreement_id)
);

CREATE TABLE participants (
    id TEXT PRIMARY KEY,
    created TIMESTAMPTZ NOT NULL,
    updated TIMESTAMPTZ NOT NULL,
    user_id TEXT NOT NULL REFERENCES users (id),
    opportunity_id TEXT NOT NULL REFERENCES opportunities (id),
    approved BOOLEAN NOT NULL,
    cancelled BOOLEAN NOT NULL,
    attended BOOLEAN NOT NULL
);

CREATE INDEX participants_opportunity_id_idx ON participants (opportunity_id);

-- A user can re-register after cancelling, so uniqueness only applies to
-- the currently active registration, not the full history. register() in
-- both backends checks this explicitly before inserting; the index is a
-- defense-in-depth backstop, not the primary mechanism.
CREATE UNIQUE INDEX participants_active_registration_idx
    ON participants (user_id, opportunity_id)
    WHERE NOT cancelled;
