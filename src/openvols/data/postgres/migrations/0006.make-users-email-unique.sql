-- An email address identifies exactly one user, regardless of case.
--
-- /api/auth/validate resolves a user by email, so duplicates made that lookup
-- ambiguous and forced an "oldest wins" tie-break. Case-insensitive because
-- people type their address inconsistently (Jane@ vs jane@), and treating
-- those as two users would split one person's registrations and sessions.
-- An expression index rather than a UNIQUE constraint, since constraints
-- can't be defined on lower(email). It also backs get_by_email's lookup.
--
-- This fails if case-insensitive duplicates already exist; resolve those
-- before applying.

CREATE UNIQUE INDEX users_email_lower_key ON users (lower(email));
