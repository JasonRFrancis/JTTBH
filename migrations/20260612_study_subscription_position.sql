-- Add position column to study_subscription for drag-to-reorder.
-- Idempotent: only adds the column if it does not already exist.

SET @dbname = DATABASE();
SET @tablename = 'study_subscription';
SET @colname = 'position';

SET @sql = IF(
  NOT EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @dbname
      AND TABLE_NAME = @tablename
      AND COLUMN_NAME = @colname
  ),
  CONCAT('ALTER TABLE `', @tablename, '` ADD COLUMN `', @colname, '` INT NOT NULL DEFAULT 0'),
  'SELECT 1'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
