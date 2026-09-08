-- Server-side sessions backing cookie authentication.
--
-- The cookie carries an opaque random token; only its SHA-256 hash is stored,
-- so a dump of this table hands out no live sessions. Unlike every other FK in
-- the schema this one cascades: a session is derived state that has no meaning
-- without its user, and DELETE /api/users/{user_id} would otherwise fail on it.
-- Related: https://github.com/briancurtin/openvols/issues/72

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created TIMESTAMPTZ,
    updated TIMESTAMPTZ,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expires TIMESTAMPTZ NOT NULL
);

CREATE OR REPLACE TRIGGER _sessions_created_at
    BEFORE INSERT ON sessions
    FOR EACH ROW
EXECUTE PROCEDURE set_created_at_timestamp();

CREATE OR REPLACE TRIGGER _sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_timestamp();

CREATE INDEX sessions_user_id_idx ON sessions (user_id);
