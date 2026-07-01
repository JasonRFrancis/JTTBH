-- Idempotent migration: add missing recipe columns + habit_entry.change_id
-- Run on production to fix recipe index error and enable habit toggle dedup.

-- recipe: add favorite, want_to_try, archived columns
ALTER TABLE `recipe`
  ADD COLUMN IF NOT EXISTS `favorite`     TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS `want_to_try`  TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS `archived`     TINYINT(1) NOT NULL DEFAULT 0;

-- habit_entry: add change_id for duplicate-toggle prevention
ALTER TABLE `habit_entry`
  ADD COLUMN IF NOT EXISTS `change_id` VARCHAR(36) NULL AFTER `vacation`,
  ADD UNIQUE KEY IF NOT EXISTS `uq_habit_entry_change_id` (`change_id`);
