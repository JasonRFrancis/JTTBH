--
-- 20260923_fitness_plan_v3.sql
-- Loads jason's training plan v3 into program aaaaaaaa-...-0001.
--   * Adds 8 exercises to the catalog (skipped if already present).
--   * Soft-deletes every current Tue–Sat program row (insert-only: new row, exerciseID NULL).
--   * Keeps Monday's leg day; appends Ab Crunch Machine to it.
--   * Inserts the Tue–Fri plan. Sets are the week 1–2 value (2); go to 3 in weeks 3–4.
--     recommended_reps is the bottom of the range; the full range is in notes.
-- Run ONCE: the program inserts are not idempotent.
--

START TRANSACTION;

INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT 'dffec448-3523-456c-934e-81300f61071a', 'Incline Dumbbell Press', 'Adjustable bench at ~30°. Upper chest.', 'hand_weight', 'hand_weight', 'chest', NULL, NOW(), NULL
WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE exerciseID = 'dffec448-3523-456c-934e-81300f61071a');
INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT 'babb87d6-a256-4b7e-8635-b94dd5d45eaa', 'Low-to-High Cable Fly', 'Cables set low, sweep up to chin height. Upper chest.', 'cable', 'machine', 'chest', NULL, NOW(), NULL
WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE exerciseID = 'babb87d6-a256-4b7e-8635-b94dd5d45eaa');
INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT 'f0c538a6-cf91-4c16-856b-3c0f50a15f19', 'Bulgarian Split Squat', 'Rear foot on bench. Glutes + quads.', 'hand_weight', 'hand_weight', 'legs', NULL, NOW(), NULL
WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE exerciseID = 'f0c538a6-cf91-4c16-856b-3c0f50a15f19');
INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT '4e50f7cd-4f6e-4d0b-83cf-543ab969bda2', 'Dumbbell Hip Thrust', 'Upper back on bench, dumbbell on hips. Glutes.', 'hand_weight', 'hand_weight', 'legs', NULL, NOW(), NULL
WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE exerciseID = '4e50f7cd-4f6e-4d0b-83cf-543ab969bda2');
INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT 'c6fbc217-3855-48b4-9094-fa470188d9a2', 'Cable Crunch', 'Kneeling, rope overhead, crunch ribs toward hips.', 'cable', 'machine', 'core', NULL, NOW(), NULL
WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE exerciseID = 'c6fbc217-3855-48b4-9094-fa470188d9a2');
INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT '18b0ef08-6757-4f3e-94d1-ae56ace397d1', 'Assisted Dip', 'Shallow: upper arm no lower than parallel. Lean forward for lower chest.', 'weight_machine', 'machine', 'chest', NULL, NOW(), NULL
WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE exerciseID = '18b0ef08-6757-4f3e-94d1-ae56ace397d1');
INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT 'b021195b-d36c-4154-bab7-f7be2d7568b9', 'Single-Arm Cable Pulldown', 'Kneeling or seated, one handle, pull elbow to hip. Lats.', 'cable', 'machine', 'back', NULL, NOW(), NULL
WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE exerciseID = 'b021195b-d36c-4154-bab7-f7be2d7568b9');
INSERT INTO fitness_exercise (exerciseID, name, description, equipment_type, type, muscle_group, video_url, created, created_by)
SELECT '32625848-6063-4208-93b4-517d0773d5be', 'Cable Lateral Raise', 'Cable low, raise slightly in front of body (scapular plane).', 'cable', 'machine', 'shoulders', NULL, NOW(), NULL
WHERE NOT EXISTS (SELECT 1 FROM fitness_exercise WHERE exerciseID = '32625848-6063-4208-93b4-517d0773d5be');

INSERT INTO fitness_program
  (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps,
   recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
SELECT fp.programID, fp.fitnessID, fp.day_of_week, NULL, fp.order_index, fp.recommended_sets, fp.recommended_reps,
       fp.recommended_weight, fp.rest_seconds, fp.notes, fp.location, fp.recommended_duration, fp.recommended_speed, fp.recommended_incline, NOW()
FROM fitness_program fp
WHERE fp.fitnessID = 'aaaaaaaa-0000-0000-0000-000000000001'
  AND fp.day_of_week BETWEEN 2 AND 6
  AND fp.exerciseID IS NOT NULL
  AND fp.id = (SELECT MAX(fp2.id) FROM fitness_program fp2 WHERE fp2.programID = fp.programID);

INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 1, '56d4a6b5-4720-11f1-85eb-22007a56be87', 101, 2, 10, NULL, NULL, '10–15 reps. If time allows.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 2, '1d96e89e-501d-458e-a6e7-09b8555952d6', 1, 2, 15, 5, NULL, 'Warm-up, each arm. Light.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 2, 'dffec448-3523-456c-934e-81300f61071a', 2, 2, 8, 20, NULL, '8–12 reps. 20–25 lb dumbbells to start.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 2, '56d48c60-4720-11f1-85eb-22007a56be87', 3, 2, 8, 95, NULL, '8–12 reps. Rest 2 min.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 2, '56d49f9e-4720-11f1-85eb-22007a56be87', 4, 2, 12, 80, NULL, '12–15 reps.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 2, 'babb87d6-a256-4b7e-8635-b94dd5d45eaa', 5, 2, 12, NULL, NULL, '12–15 reps. Superset with pushdown.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 2, '56d4a4b9-4720-11f1-85eb-22007a56be87', 6, 2, 10, NULL, NULL, '10–15 reps, rope. Superset with fly. Don''t snap into lockout (elbow).', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 2, '738dbbc3-5771-11f1-b045-22007a56be87', 7, NULL, NULL, NULL, NULL, 'After lifting.', 'gym', 20, 3.5, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, '1d96e89e-501d-458e-a6e7-09b8555952d6', 1, 2, 15, 5, NULL, 'Warm-up, each arm. Light.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, '56d48ee4-4720-11f1-85eb-22007a56be87', 2, 2, 8, 140, NULL, '8–12 reps, neutral grip. Rest 2 min.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, '7b07a014-5ed6-4ee1-91b4-585f7f047519', 3, 2, NULL, 46, NULL, 'As many reps as possible. Lower the assist over time.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, '56d48f3b-4720-11f1-85eb-22007a56be87', 4, 2, 10, 65, NULL, '10–12 reps, neutral grip.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, '56d49ff6-4720-11f1-85eb-22007a56be87', 5, 2, 12, 100, NULL, '12–15 reps. Superset with shrug.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, '56d4b6e7-4720-11f1-85eb-22007a56be87', 6, 2, 10, 65, NULL, '10–15 reps, use straps. Superset with rear delt fly.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, 'c0d3e7f7-440c-4dfe-b84a-379e319eaea5', 7, 2, 12, 40, NULL, '12–15 reps.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 3, '738dbbc3-5771-11f1-b045-22007a56be87', 8, NULL, NULL, NULL, NULL, 'After lifting.', 'gym', 20, 3.5, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 4, 'f0c538a6-cf91-4c16-856b-3c0f50a15f19', 1, 2, 8, NULL, NULL, '8–12 reps each leg. Bodyweight first, then a dumbbell in the right hand.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 4, '4e50f7cd-4f6e-4d0b-83cf-543ab969bda2', 2, 2, 8, NULL, NULL, '8–12 reps.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 4, '56d4562d-4720-11f1-85eb-22007a56be87', 3, 2, 12, 150, NULL, '12–15 reps.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 4, '14d07e81-57ad-11f1-b045-22007a56be87', 4, 2, 10, NULL, NULL, '10–15 reps, captain''s chair. Superset with cable crunch.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 4, 'c6fbc217-3855-48b4-9094-fa470188d9a2', 5, 2, 10, NULL, NULL, '10–15 reps. Superset with leg raise.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 4, '738dbbc3-5771-11f1-b045-22007a56be87', 6, NULL, NULL, NULL, NULL, 'Long walk day: 30–40 min.', 'gym', 30, 3.5, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 5, '1d96e89e-501d-458e-a6e7-09b8555952d6', 1, 2, 15, 5, NULL, 'Warm-up, each arm. Light.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 5, '56d49f48-4720-11f1-85eb-22007a56be87', 2, 2, 8, 70, NULL, '8–10 reps, neutral grip. Rest 2 min.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 5, '18b0ef08-6757-4f3e-94d1-ae56ace397d1', 3, 2, 8, NULL, NULL, '8–12 reps. Lots of assist; shallow. Swap for cable fly if right shoulder pinches.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 5, 'b021195b-d36c-4154-bab7-f7be2d7568b9', 4, 2, 10, NULL, NULL, '10–12 reps each arm.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 5, '56d48cb5-4720-11f1-85eb-22007a56be87', 5, 2, 10, 115, NULL, '10–12 reps.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 5, '32625848-6063-4208-93b4-517d0773d5be', 6, 2, 12, NULL, NULL, '12–15 reps each arm. Superset with tricep machine.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 5, '56d4a3bd-4720-11f1-85eb-22007a56be87', 7, 2, 10, 85, NULL, '10–12 reps. Superset with lateral raise.', 'gym', NULL, NULL, NULL, NOW());
INSERT INTO fitness_program (programID, fitnessID, day_of_week, exerciseID, order_index, recommended_sets, recommended_reps, recommended_weight, rest_seconds, notes, location, recommended_duration, recommended_speed, recommended_incline, created)
VALUES (UUID(), 'aaaaaaaa-0000-0000-0000-000000000001', 5, '738dbbc3-5771-11f1-b045-22007a56be87', 8, NULL, NULL, NULL, NULL, 'After lifting.', 'gym', 20, 3.5, NULL, NOW());

COMMIT;
