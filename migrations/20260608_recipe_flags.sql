-- Add favorite and want_to_try flags to recipe (insert-only table)
ALTER TABLE recipe
  ADD COLUMN IF NOT EXISTS favorite    TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS want_to_try TINYINT(1) NOT NULL DEFAULT 0;
