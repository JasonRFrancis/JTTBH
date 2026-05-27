-- Migration: Replace 'bodyweight' exercise type with 'done'
-- Date: 2026-05-27
--
-- 'bodyweight' exercises all tracked sets×reps identical to 'strength'.
-- Replace with 'done' type for video/tutorial exercises that just record completion.
--
-- 1. Migrate existing bodyweight rows → strength (before altering the enum)
-- 2. Alter the enum to swap 'bodyweight' for 'done'

UPDATE fitness_exercise SET `type` = 'strength' WHERE `type` = 'bodyweight';

ALTER TABLE fitness_exercise
  MODIFY COLUMN `type` enum('strength','cardio','done') NOT NULL DEFAULT 'strength';

-- Rollback:
-- ALTER TABLE fitness_exercise
--   MODIFY COLUMN `type` enum('strength','cardio','bodyweight') NOT NULL DEFAULT 'strength';
-- (re-typing individual exercises back to 'bodyweight' would need manual work)
