-- Migration: Fitness goal-specific exercises
-- Date: 2026-05-24
-- Author: jason
-- Depends on: 20260524_fitness_setup.sql (must run first)
--
-- Goals: broader shoulders, upper chest, back thickness/width,
--        forearm definition, abs/obliques definition
--
-- Adds:
--   1. New exercises to the catalog (bodyweight + forearm)
--   2. Gym day expansions (Mon: core; Wed: upper chest, T-bar row, hammer curl)
--   3. Home day programs (Tue/Thu/Fri/Sat)

-- ---------------------------------------------------------------------------
-- 1. New exercise catalog entries (idempotent)
-- ---------------------------------------------------------------------------

INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT UUID(), 'Push-up', 'Standard push-up targeting chest, shoulders, and triceps', 'bodyweight', 'bodyweight', 'chest', NULL, NOW(), NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE name = 'Push-up');

INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT UUID(), 'Pike Push-up', 'Inverted V push-up that loads the shoulders like an overhead press', 'bodyweight', 'bodyweight', 'shoulders', NULL, NOW(), NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE name = 'Pike Push-up');

INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT UUID(), 'Plank', 'Isometric core hold — builds deep stabilizer strength', 'bodyweight', 'bodyweight', 'core', NULL, NOW(), NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE name = 'Plank');

INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT UUID(), 'Bicycle Crunch', 'Alternating elbow-to-knee crunch targeting abs and obliques', 'bodyweight', 'bodyweight', 'core', NULL, NOW(), NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE name = 'Bicycle Crunch');

INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT UUID(), 'Russian Twist', 'Seated trunk rotation — primary oblique builder', 'bodyweight', 'bodyweight', 'core', NULL, NOW(), NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE name = 'Russian Twist');

INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT UUID(), 'Leg Raise', 'Lying leg raise targeting lower abs', 'bodyweight', 'bodyweight', 'core', NULL, NOW(), NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE name = 'Leg Raise');

INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT UUID(), 'Dumbbell Reverse Curl', 'Overhand-grip curl — builds brachioradialis and forearm extensors', 'hand_weight', 'strength', 'forearms', NULL, NOW(), NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE name = 'Dumbbell Reverse Curl');

INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT UUID(), 'Dumbbell Wrist Curl', 'Palm-up wrist flexion — targets forearm flexors', 'hand_weight', 'strength', 'forearms', NULL, NOW(), NULL
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE name = 'Dumbbell Wrist Curl');

-- ---------------------------------------------------------------------------
-- 2. Monday (day_of_week=1) — Add core at the end of gym day
-- ---------------------------------------------------------------------------

-- Ab Crunch Machine  3 × 15
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 1, exerciseID, 9, 3, 15, NULL, NULL, 'gym', NOW()
FROM fitness_exercise WHERE name = 'Ab Crunch Machine' LIMIT 1;

-- Torso Rotation Machine  3 × 15 each side
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 1, exerciseID, 10, 3, 15, NULL, 'each side', 'gym', NOW()
FROM fitness_exercise WHERE name = 'Torso Rotation Machine' LIMIT 1;

-- ---------------------------------------------------------------------------
-- 3. Wednesday (day_of_week=3) — Add upper chest, back thickness, forearms
-- ---------------------------------------------------------------------------

-- Incline Chest Press  2 × 8  (upper chest — key for chest-line definition)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, exerciseID, 11, 2, 8, NULL, NULL, 'gym', NOW()
FROM fitness_exercise WHERE name = 'Incline Chest Press' LIMIT 1;

-- T-Bar Row  2 × 8  (back thickness — different angle than seated row)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, exerciseID, 12, 2, 8, NULL, NULL, 'gym', NOW()
FROM fitness_exercise WHERE name = 'T-Bar Row' LIMIT 1;

-- Dumbbell Hammer Curl  2 × 10  (brachioradialis / forearm bulk)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, exerciseID, 13, 2, 10, NULL, NULL, 'gym', NOW()
FROM fitness_exercise WHERE name = 'Dumbbell Hammer Curl' LIMIT 1;

-- ---------------------------------------------------------------------------
-- 4. Tuesday (day_of_week=2) — Home: shoulders + push
-- ---------------------------------------------------------------------------

-- Push-up  3 × 20  (chest/shoulders/triceps — no equipment)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 2, exerciseID, 1, 3, 20, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Push-up' LIMIT 1;

-- Pike Push-up  3 × 10  (shoulder caps — most effective at-home shoulder builder)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 2, exerciseID, 2, 3, 10, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Pike Push-up' LIMIT 1;

-- Dumbbell Lateral Raise  3 × 12  (shoulder width)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 2, exerciseID, 3, 3, 12, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Dumbbell Lateral Raise' LIMIT 1;

-- Dumbbell Front Raise  2 × 10  (front delt / upper chest line)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 2, exerciseID, 4, 2, 10, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Dumbbell Front Raise' LIMIT 1;

-- ---------------------------------------------------------------------------
-- 5. Thursday (day_of_week=4) — Home: core
-- ---------------------------------------------------------------------------

-- Plank  3 × 60 sec
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 4, exerciseID, 1, 3, 60, NULL, 'sec per set', 'home', NOW()
FROM fitness_exercise WHERE name = 'Plank' LIMIT 1;

-- Bicycle Crunch  3 × 20  (abs + obliques)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 4, exerciseID, 2, 3, 20, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Bicycle Crunch' LIMIT 1;

-- Russian Twist  3 × 20  (obliques)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 4, exerciseID, 3, 3, 20, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Russian Twist' LIMIT 1;

-- Leg Raise  3 × 12  (lower abs)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 4, exerciseID, 4, 3, 12, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Leg Raise' LIMIT 1;

-- ---------------------------------------------------------------------------
-- 6. Friday (day_of_week=5) — Home: forearms + back supplement
-- ---------------------------------------------------------------------------

-- Dumbbell Reverse Curl  3 × 12  (forearm extensors / brachioradialis)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 5, exerciseID, 1, 3, 12, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Dumbbell Reverse Curl' LIMIT 1;

-- Dumbbell Wrist Curl  3 × 15  (forearm flexors)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 5, exerciseID, 2, 3, 15, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Dumbbell Wrist Curl' LIMIT 1;

-- Dumbbell Hammer Curl  3 × 10  (brachioradialis — complements wrist curls)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 5, exerciseID, 3, 3, 10, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Dumbbell Hammer Curl' LIMIT 1;

-- Dumbbell Bent-Over Row  3 × 10  (back thickness supplement)
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 5, exerciseID, 4, 3, 10, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Dumbbell Bent-Over Row' LIMIT 1;

-- ---------------------------------------------------------------------------
-- 7. Saturday (day_of_week=6) — Home: maintenance / mixed
-- ---------------------------------------------------------------------------

-- Push-up  2 × 15
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 6, exerciseID, 1, 2, 15, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Push-up' LIMIT 1;

-- Pike Push-up  2 × 10
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 6, exerciseID, 2, 2, 10, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Pike Push-up' LIMIT 1;

-- Russian Twist  2 × 20
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 6, exerciseID, 3, 2, 20, NULL, NULL, 'home', NOW()
FROM fitness_exercise WHERE name = 'Russian Twist' LIMIT 1;

-- Plank  2 × 60 sec
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, notes, location, created)
SELECT UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 6, exerciseID, 4, 2, 60, NULL, 'sec per set', 'home', NOW()
FROM fitness_exercise WHERE name = 'Plank' LIMIT 1;

-- Rollback (comment out, for reference):
-- DELETE FROM fitness_program
--   WHERE fitnessID = 'aaaaaaaa-0000-0000-0000-000000000001'
--   AND day_of_week IN (2, 4, 5, 6);
-- DELETE FROM fitness_program
--   WHERE fitnessID = 'aaaaaaaa-0000-0000-0000-000000000001'
--   AND day_of_week = 1 AND order_index IN (9, 10);
-- DELETE FROM fitness_program
--   WHERE fitnessID = 'aaaaaaaa-0000-0000-0000-000000000001'
--   AND day_of_week = 3 AND order_index IN (11, 12, 13);
