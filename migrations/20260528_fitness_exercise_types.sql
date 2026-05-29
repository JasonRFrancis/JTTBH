-- Migration: Fitness exercise type system overhaul
-- Date: 2026-05-28
--
-- Replaces 3-type system (strength/cardio/done) with 5 types:
--   machine     — weight machine: logs setup, weight, reps, notes
--   hand_weight — dumbbells/barbells: logs weight, reps, notes
--   bodyweight  — push-ups etc: logs reps, time (sec), notes
--   cardio      — treadmill etc: logs setup, time (min), speed, notes
--   video       — tutorial/form video: logs notes (row = accomplished)
--
-- Also adds fitness_logSet.setup: captures per-session machine/cardio
-- setup notes (seat position, resistance, etc.) separately from general
-- notes. Existing logSet.notes values (always setup info) migrate over.

-- ---------------------------------------------------------------------------
-- 1. Add setup column to fitness_logSet
-- ---------------------------------------------------------------------------
ALTER TABLE fitness_logSet
  ADD COLUMN `setup` varchar(255) DEFAULT NULL AFTER notes;

-- ---------------------------------------------------------------------------
-- 2. Migrate existing logSet.notes → setup
--    (all pre-existing notes values were adjustment notes, not general notes)
-- ---------------------------------------------------------------------------
UPDATE fitness_logSet SET setup = notes, notes = NULL WHERE notes IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 3. Expand enum to allow both old and new values simultaneously
-- ---------------------------------------------------------------------------
ALTER TABLE fitness_exercise MODIFY COLUMN `type`
  ENUM('strength','cardio','done','machine','hand_weight','bodyweight','video')
  NOT NULL DEFAULT 'machine';

-- ---------------------------------------------------------------------------
-- 4. Map old values → new values using equipment_type as the guide
-- ---------------------------------------------------------------------------
UPDATE fitness_exercise SET `type` = 'machine'
  WHERE `type` = 'strength' AND equipment_type IN ('weight_machine', 'cable', 'other');

UPDATE fitness_exercise SET `type` = 'hand_weight'
  WHERE `type` = 'strength' AND equipment_type = 'hand_weight';

UPDATE fitness_exercise SET `type` = 'bodyweight'
  WHERE `type` = 'strength' AND equipment_type = 'bodyweight';

-- Safety net: any remaining 'strength' rows become 'machine'
UPDATE fitness_exercise SET `type` = 'machine' WHERE `type` = 'strength';

UPDATE fitness_exercise SET `type` = 'video' WHERE `type` = 'done';

-- ---------------------------------------------------------------------------
-- 5. Shrink enum to final set (removes old values from the column definition)
-- ---------------------------------------------------------------------------
ALTER TABLE fitness_exercise MODIFY COLUMN `type`
  ENUM('machine','hand_weight','bodyweight','cardio','video')
  NOT NULL DEFAULT 'machine';

-- Rollback:
-- ALTER TABLE fitness_exercise MODIFY COLUMN `type`
--   ENUM('machine','hand_weight','bodyweight','cardio','video','strength','done')
--   NOT NULL DEFAULT 'machine';
-- (full data rollback would require re-running the old migration to restore old values)
-- ALTER TABLE fitness_logSet DROP COLUMN IF EXISTS setup;
