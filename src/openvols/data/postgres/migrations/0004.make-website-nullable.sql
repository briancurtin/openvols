-- Store empty website values as NULL instead of ''
-- Related https://github.com/briancurtin/openvols/issues/15

ALTER TABLE organizations ALTER COLUMN website DROP NOT NULL;
