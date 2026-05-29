# Fitness Feature — Implementation Plan

## Schema changes
- [x] Add `created_by` to `fitness` + `fitness_exercise`
- [x] Add `type` enum('strength','cardio','done') to `fitness_exercise`
- [x] Add `location`, `recommended_duration`, `recommended_speed`, `recommended_incline` to `fitness_program`
- [x] Add `duration_minutes`, `speed`, `incline` to `fitness_logSet`
- [x] Add `fitness_bodyWeight` table
- [x] Update `schema.sql` with all of the above
- [x] Write `migrations/20260524_fitness_setup.sql`

## Seed data (migration)
- [x] Add Treadmill to `fitness_exercise`
- [x] Seed default program "My Program" for admin user (fitnessID = aaaaaaaa-0000-0000-0000-000000000001)
- [x] Seed Monday lower-body exercises (with recent weights from log)
- [x] Seed Wednesday upper-body exercises (with recent weights from log)
- [x] Leave Tue/Thu/Fri/Sat as empty home days (user configures)

## Python
- [x] `app/models/fitness_model.py` — all model methods
- [x] `app/routes/fitness.py` — rewrite with full route set

## Templates
- [x] `app/templates/fitness_index.html` — today's workout + body weight + inline set logging
- [x] `app/templates/fitness_settings.html` — program management, day-by-day exercise editor
- [x] `app/templates/fitness_log.html` — workout history with sets

## Static
- [x] `app/static/css/fitness.css` — rewrite mobile-first
- [x] `app/static/js/fitness.js` — AJAX set logging

## Verify
- [x] Run app, visit fitness index, log a set
- [x] Verify body weight saves
- [x] Verify settings page shows exercises per day, add/remove works
- [x] Verify log history shows sets
