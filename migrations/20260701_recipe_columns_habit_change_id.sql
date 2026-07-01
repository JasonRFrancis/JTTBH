-- Idempotent migration: add missing recipe columns + habit_entry.change_id
-- MySQL-compatible (no ADD COLUMN IF NOT EXISTS — that's MariaDB only)

DROP PROCEDURE IF EXISTS _migrate_20260701;
DELIMITER $$
CREATE PROCEDURE _migrate_20260701()
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'recipe' AND COLUMN_NAME = 'favorite'
  ) THEN
    ALTER TABLE `recipe`
      ADD COLUMN `favorite`    TINYINT(1) NOT NULL DEFAULT 0,
      ADD COLUMN `want_to_try` TINYINT(1) NOT NULL DEFAULT 0,
      ADD COLUMN `archived`    TINYINT(1) NOT NULL DEFAULT 0;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'habit_entry' AND COLUMN_NAME = 'change_id'
  ) THEN
    ALTER TABLE `habit_entry`
      ADD COLUMN `change_id` VARCHAR(36) NULL AFTER `vacation`,
      ADD UNIQUE KEY `uq_habit_entry_change_id` (`change_id`);
  END IF;
END$$
DELIMITER ;

CALL _migrate_20260701();
DROP PROCEDURE IF EXISTS _migrate_20260701;
