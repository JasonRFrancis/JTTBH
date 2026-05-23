-- Add change_id to habit_entry for idempotent toggle requests.
-- Idempotent: safe to run multiple times.

ALTER TABLE `habit_entry`
  ADD COLUMN IF NOT EXISTS `change_id` varchar(36) DEFAULT NULL
    COMMENT 'Client-generated UUID per toggle request; UNIQUE prevents duplicate processing on retry'
    AFTER `vacation`,
  ADD UNIQUE KEY IF NOT EXISTS `uniq_change_id` (`change_id`);
