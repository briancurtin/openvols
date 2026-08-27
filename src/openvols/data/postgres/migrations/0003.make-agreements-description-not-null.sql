-- Agreement.description now requires a substantive value (min_length=10), so
-- empty-as-NULL storage no longer applies here. See the discussion on #15.

ALTER TABLE agreements ALTER COLUMN description SET NOT NULL;
