-- Add archived flag to recipe (insert-only table)
ALTER TABLE recipe
  ADD COLUMN archived TINYINT(1) NOT NULL DEFAULT 0;
