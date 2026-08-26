-- Store empty phone/description/notes values as NULL instead of ''
-- to save on storage and keep query planning/indexing cleaner.
-- See https://github.com/briancurtin/openvols/issues/15

ALTER TABLE organizations ALTER COLUMN phone DROP NOT NULL;
ALTER TABLE users ALTER COLUMN phone DROP NOT NULL;
ALTER TABLE agreements ALTER COLUMN description DROP NOT NULL;
ALTER TABLE opportunities ALTER COLUMN notes DROP NOT NULL;
