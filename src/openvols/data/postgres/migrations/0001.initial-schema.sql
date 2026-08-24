-- Initial schema for the Postgres Store backend.
--
-- ids/created/updated are set by application code (see
-- openvols.data.postgres._store), not database defaults, so every backend
-- generates them the same way.

CREATE OR REPLACE FUNCTION set_created_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.created = NOW();
    -- Initialize updated_at as well so we don't need to compare against
    -- `created_at is null` to know if it's never been updated.
    NEW.updated = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';


CREATE OR REPLACE FUNCTION update_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';


CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created TIMESTAMPTZ,
    updated TIMESTAMPTZ,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    website TEXT NOT NULL,
    contact TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    private_allowed BOOLEAN NOT NULL,
    approved BOOLEAN NOT NULL
);

CREATE OR REPLACE TRIGGER _organizations_created_at
    BEFORE INSERT ON organizations
    FOR EACH ROW
EXECUTE PROCEDURE set_created_at_timestamp();


CREATE OR REPLACE TRIGGER _organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_timestamp();

CREATE TABLE IF NOT EXISTS users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created TIMESTAMPTZ,
    updated TIMESTAMPTZ,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    email_reminders BOOLEAN NOT NULL,
    phone TEXT NOT NULL,
    phone_reminders BOOLEAN NOT NULL
);

CREATE OR REPLACE TRIGGER _users_created_at
    BEFORE INSERT ON users
    FOR EACH ROW
EXECUTE PROCEDURE set_created_at_timestamp();


CREATE OR REPLACE TRIGGER _users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_timestamp();

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created TIMESTAMPTZ,
    updated TIMESTAMPTZ,
    organization_id INTEGER NOT NULL REFERENCES organizations (id),
    user_id INTEGER NOT NULL REFERENCES users (id),
    type SMALLINT NOT NULL
);

CREATE OR REPLACE TRIGGER _roles_created_at
    BEFORE INSERT ON roles
    FOR EACH ROW
EXECUTE PROCEDURE set_created_at_timestamp();


CREATE OR REPLACE TRIGGER _roles_updated_at
    BEFORE UPDATE ON roles
    FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_timestamp();

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created TIMESTAMPTZ,
    updated TIMESTAMPTZ,
    organization_id INTEGER NOT NULL REFERENCES organizations (id),
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    country TEXT NOT NULL
);

CREATE OR REPLACE TRIGGER _locations_created_at
    BEFORE INSERT ON locations
    FOR EACH ROW
EXECUTE PROCEDURE set_created_at_timestamp();


CREATE OR REPLACE TRIGGER _locations_updated_at
    BEFORE UPDATE ON locations
    FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_timestamp();

CREATE TABLE IF NOT EXISTS agreements (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created TIMESTAMPTZ,
    updated TIMESTAMPTZ,
    organization_id INTEGER NOT NULL REFERENCES organizations (id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    content TEXT NOT NULL,
    valid TIMESTAMPTZ NOT NULL,
    invalid TIMESTAMPTZ NOT NULL,
    cadence TEXT NOT NULL
);

CREATE OR REPLACE TRIGGER _agreements_created_at
    BEFORE INSERT ON agreements
    FOR EACH ROW
EXECUTE PROCEDURE set_created_at_timestamp();


CREATE OR REPLACE TRIGGER _agreements_updated_at
    BEFORE UPDATE ON agreements
    FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_timestamp();

-- start/end are reserved words, so the columns are named to avoid quoting
-- every reference to them throughout the query layer.
CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created TIMESTAMPTZ,
    updated TIMESTAMPTZ,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    location_id INTEGER NOT NULL REFERENCES locations (id),
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    public BOOLEAN NOT NULL,
    open BOOLEAN NOT NULL,
    cancelled BOOLEAN NOT NULL,
    completed BOOLEAN NOT NULL,
    contact_id INTEGER NOT NULL REFERENCES users (id),
    capacity INTEGER NOT NULL CHECK (capacity >= 0),
    notes TEXT NOT NULL,
    auto_approve_registrants BOOLEAN NOT NULL,
    auto_approve_waiters BOOLEAN NOT NULL
);

CREATE OR REPLACE TRIGGER _opportunities_created_at
    BEFORE INSERT ON opportunities
    FOR EACH ROW
EXECUTE PROCEDURE set_created_at_timestamp();

CREATE OR REPLACE TRIGGER _opportunities_updated_at
    BEFORE UPDATE ON opportunities
    FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_timestamp();

CREATE TABLE IF NOT EXISTS opportunity_agreements (
    opportunity_id INTEGER NOT NULL REFERENCES opportunities (id),
    agreement_id INTEGER NOT NULL REFERENCES agreements (id),
    PRIMARY KEY (opportunity_id, agreement_id)
);

CREATE TABLE IF NOT EXISTS participants (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created TIMESTAMPTZ,
    updated TIMESTAMPTZ,
    user_id INTEGER NOT NULL REFERENCES users (id),
    opportunity_id INTEGER NOT NULL REFERENCES opportunities (id),
    approved BOOLEAN NOT NULL,
    cancelled BOOLEAN NOT NULL,
    attended BOOLEAN NOT NULL
);

CREATE OR REPLACE TRIGGER _participants_created_at
    BEFORE INSERT ON participants
    FOR EACH ROW
EXECUTE PROCEDURE set_created_at_timestamp();

CREATE OR REPLACE TRIGGER _participants_updated_at
    BEFORE UPDATE ON participants
    FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_timestamp();

CREATE INDEX participants_opportunity_id_idx ON participants (opportunity_id);

-- A user can re-register after cancelling, so uniqueness only applies to
-- the currently active registration, not the full history. register() in
-- both backends checks this explicitly before inserting; the index is a
-- defense-in-depth backstop, not the primary mechanism.
CREATE UNIQUE INDEX participants_active_registration_idx
    ON participants (user_id, opportunity_id)
    WHERE NOT cancelled;
