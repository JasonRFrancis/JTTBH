-- Split 'game' kind into 'videogame' and 'boardgame'.
-- Expand → update → contract ENUM pattern.
-- Run after 20260529_media_import.sql.

-- 1. Expand to include all values
ALTER TABLE media
  MODIFY COLUMN kind ENUM('book','movie','show','podcast','game','videogame','boardgame') NOT NULL DEFAULT 'book';

-- 2. Migrate existing rows
UPDATE media SET kind = 'videogame' WHERE kind = 'game';

-- 3. Contract to remove 'game'
ALTER TABLE media
  MODIFY COLUMN kind ENUM('book','movie','show','podcast','videogame','boardgame') NOT NULL DEFAULT 'book';
