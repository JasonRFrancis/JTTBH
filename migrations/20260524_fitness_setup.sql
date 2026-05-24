-- Migration: Fitness feature setup
-- Date: 2026-05-24
-- Author: jason
--
-- 1. Add missing audit columns to fitness tables
-- 2. Add exercise type (strength / cardio / bodyweight)
-- 3. Add cardio tracking columns to fitness_logSet
-- 4. Add per-day location and cardio recommendations to fitness_program
-- 5. Create fitness_bodyWeight table
-- 6. Add Treadmill to exercise catalog
-- 7. Seed default program for admin user

-- ---------------------------------------------------------------------------
-- 1. fitness: add created_by
-- ---------------------------------------------------------------------------

ALTER TABLE fitness
  ADD COLUMN `created_by` varchar(36) DEFAULT NULL AFTER created;

-- ---------------------------------------------------------------------------
-- 2. fitness_exercise: add created_by + type
-- ---------------------------------------------------------------------------

ALTER TABLE fitness_exercise
  ADD COLUMN `created_by` varchar(36) DEFAULT NULL AFTER created,
  ADD COLUMN `type` enum('strength','cardio','bodyweight') NOT NULL DEFAULT 'strength' AFTER video_url;

-- ---------------------------------------------------------------------------
-- 3. fitness_program: add location + cardio recommendation columns
-- ---------------------------------------------------------------------------

ALTER TABLE fitness_program
  ADD COLUMN `location`             enum('gym','home','other') NOT NULL DEFAULT 'gym' AFTER notes,
  ADD COLUMN `recommended_duration` int DEFAULT NULL AFTER location,
  ADD COLUMN `recommended_speed`    decimal(4,2) DEFAULT NULL AFTER recommended_duration,
  ADD COLUMN `recommended_incline`  decimal(4,1) DEFAULT NULL AFTER recommended_speed;

-- ---------------------------------------------------------------------------
-- 4. fitness_logSet: add cardio logging columns
-- ---------------------------------------------------------------------------

ALTER TABLE fitness_logSet
  ADD COLUMN `duration_minutes` int DEFAULT NULL AFTER notes,
  ADD COLUMN `speed`            decimal(4,2) DEFAULT NULL AFTER duration_minutes,
  ADD COLUMN `incline`          decimal(4,1) DEFAULT NULL AFTER speed;

-- ---------------------------------------------------------------------------
-- 5. fitness_bodyWeight: new table
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `fitness_bodyWeight` (
  `id` int NOT NULL AUTO_INCREMENT,
  `weightID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `weight` decimal(5,1) NOT NULL,
  `unit` enum('lbs','kg') NOT NULL DEFAULT 'lbs',
  `recorded` date NOT NULL,
  `created` datetime NOT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_weightID` (`weightID`),
  KEY `idx_userID_recorded` (`userID`, `recorded`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 6. Add Treadmill to exercise catalog
-- ---------------------------------------------------------------------------

INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT UUID(), 'Treadmill', 'Incline treadmill walk', 'other', 'cardio', 'cardio', NULL, NOW(), NULL
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE name = 'Treadmill');

-- ---------------------------------------------------------------------------
-- 7. Seed default program for admin user
-- ---------------------------------------------------------------------------

-- Create the program (idempotent via INSERT IGNORE on fixed fitnessID)
INSERT IGNORE INTO fitness (fitnessID, userID, name, description, start_date, active, created, created_by)
VALUES (
  'aaaaaaaa-0000-0000-0000-000000000001',
  '58ec8c11-e060-4367-93cf-91a6cc28db8c',
  'My Program',
  'Gym Mon/Wed; home exercises Tue/Thu/Fri/Sat',
  '2026-01-06',
  1,
  NOW(),
  '58ec8c11-e060-4367-93cf-91a6cc28db8c'
);

-- Clear any existing program exercises so this block is idempotent
DELETE FROM fitness_program WHERE fitnessID = 'aaaaaaaa-0000-0000-0000-000000000001';

-- ── Monday (day_of_week=1) — Lower body — Gym ─────────────────────────────

-- Seated Calf Raise  adj:13  315 × 15 × 5
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 1, exerciseID, 1, 5, 15, 315, '13', 'gym', NOW()
FROM fitness_exercise WHERE name = 'Seated Calf Raise' LIMIT 1;

-- Standing Calf Raise  adj:7  160 × 10 × 3
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 1, exerciseID, 2, 3, 10, 160, '7', 'gym', NOW()
FROM fitness_exercise WHERE name = 'Standing Calf Raise' LIMIT 1;

-- Hip Abductor  170 × 10 × 2
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 1, exerciseID, 3, 2, 10, 170, NULL, 'gym', NOW()
FROM fitness_exercise WHERE name = 'Hip Abductor' LIMIT 1;

-- Hip Adductor  adj:6  155 × 10 × 2
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 1, exerciseID, 4, 2, 10, 155, '6', 'gym', NOW()
FROM fitness_exercise WHERE name = 'Hip Adductor' LIMIT 1;

-- Leg Curl  adj:2  120 × 5 × 2
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 1, exerciseID, 5, 2, 5, 120, '2', 'gym', NOW()
FROM fitness_exercise WHERE name = 'Leg Curl' LIMIT 1;

-- Leg Extension  140 × 10 × 2
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 1, exerciseID, 6, 2, 10, 140, NULL, 'gym', NOW()
FROM fitness_exercise WHERE name = 'Leg Extension' LIMIT 1;

-- Leg Press  310 × 10 × 2
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 1, exerciseID, 7, 2, 10, 310, NULL, 'gym', NOW()
FROM fitness_exercise WHERE name = 'Leg Press' LIMIT 1;

-- Treadmill  15° incline, 10 min, 2.4 mph
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 1, exerciseID, 8, NULL, NULL, NULL, NULL, 'gym', 10, 2.4, 15.0, NOW()
FROM fitness_exercise WHERE name = 'Treadmill' LIMIT 1;

-- ── Wednesday (day_of_week=3) — Upper body — Gym ──────────────────────────

-- Chest Press Machine  adj:5  90 × 5 × 2
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, exerciseID, 1, 2, 5, 90, '5', 'gym', NOW()
FROM fitness_exercise WHERE name = 'Chest Press Machine' LIMIT 1;

-- Lat Pulldown  155 × 5 × 2
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, exerciseID, 2, 2, 5, 155, NULL, 'gym', NOW()
FROM fitness_exercise WHERE name = 'Lat Pulldown' LIMIT 1;

-- Pec Fly Machine  130 × 5 × 2
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, exerciseID, 3, 2, 5, 130, NULL, 'gym', NOW()
FROM fitness_exercise WHERE name = 'Pec Fly Machine' LIMIT 1;

-- Rear Delt Fly Machine  110 × 5 × 2
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, exerciseID, 4, 2, 5, 110, NULL, 'gym', NOW()
FROM fitness_exercise WHERE name = 'Rear Delt Fly Machine' LIMIT 1;

-- Seated Cable Row  150 × 10 × 2
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, exerciseID, 5, 2, 10, 150, NULL, 'gym', NOW()
FROM fitness_exercise WHERE name = 'Seated Cable Row' LIMIT 1;

-- Lateral Raise Machine  adj:5  80 × 5 × 2
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, exerciseID, 6, 2, 5, 80, '5', 'gym', NOW()
FROM fitness_exercise WHERE name = 'Lateral Raise Machine' LIMIT 1;

-- Shoulder Press Machine  adj:3  80 × 5 × 2
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, exerciseID, 7, 2, 5, 80, '3', 'gym', NOW()
FROM fitness_exercise WHERE name = 'Shoulder Press Machine' LIMIT 1;

-- Bicep Curl Machine  adj:2  95 × 5 × 2
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, exerciseID, 8, 2, 5, 95, '2', 'gym', NOW()
FROM fitness_exercise WHERE name = 'Bicep Curl Machine' LIMIT 1;

-- Tricep Extension Machine  adj:2,6  95 × 5 × 1
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, exerciseID, 9, 1, 5, 95, '2, 6', 'gym', NOW()
FROM fitness_exercise WHERE name = 'Tricep Extension Machine' LIMIT 1;

-- Treadmill  15° incline, 10 min, 2.4 mph
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, exerciseID, 10, NULL, NULL, NULL, NULL, 'gym', 10, 2.4, 15.0, NOW()
FROM fitness_exercise WHERE name = 'Treadmill' LIMIT 1;

-- Rollback (comment out, for reference):
-- DELETE FROM fitness_program WHERE fitnessID = 'aaaaaaaa-0000-0000-0000-000000000001';
-- DELETE FROM fitness WHERE fitnessID = 'aaaaaaaa-0000-0000-0000-000000000001';
-- DROP TABLE IF EXISTS fitness_bodyWeight;
-- ALTER TABLE fitness_logSet DROP COLUMN IF EXISTS duration_minutes, DROP COLUMN IF EXISTS speed, DROP COLUMN IF EXISTS incline;
-- ALTER TABLE fitness_program DROP COLUMN IF EXISTS location, DROP COLUMN IF EXISTS recommended_duration, DROP COLUMN IF EXISTS recommended_speed, DROP COLUMN IF EXISTS recommended_incline;
-- ALTER TABLE fitness_exercise DROP COLUMN IF EXISTS type, DROP COLUMN IF EXISTS created_by;
-- ALTER TABLE fitness DROP COLUMN IF EXISTS created_by;
