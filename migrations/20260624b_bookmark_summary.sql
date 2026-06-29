-- Add summary column to bookmark table.
-- Stores the persisted AI/agent summary for a bookmarked page.
-- Idempotent: safe to re-run.

SET @s = (SELECT IF(
    EXISTS(
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'bookmark'
          AND COLUMN_NAME  = 'summary'
    ),
    'SELECT 1',
    'ALTER TABLE bookmark ADD COLUMN summary TEXT NULL'
));
PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
