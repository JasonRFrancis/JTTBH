# Fitness Feature — Implementation Plan

## Schema changes
- [x] Add `created_by` to `fitness` + `fitness_exercise`
- [x] Add `type` enum('strength','cardio','bodyweight') to `fitness_exercise`
- [x] Add `location`, `recommended_duration`, `recommended_speed`, `recommended_incline` to `fitness_program`
- [x] Add `duration_minutes`, `speed`, `incline` to `fitness_logSet`
- [x] Add `fitness_bodyWeight` table
- [ ] Update `schema.sql` with all of the above
- [ ] Write `migrations/20260524_fitness_setup.sql`

## Seed data (migration)
- [ ] Add Treadmill to `fitness_exercise`
- [ ] Seed default program "My Program" for admin user (fitnessID = aaaaaaaa-0000-0000-0000-000000000001)
- [ ] Seed Monday lower-body exercises (with recent weights from log)
- [ ] Seed Wednesday upper-body exercises (with recent weights from log)
- [ ] Leave Tue/Thu/Fri/Sat as empty home days (user configures)

## Python
- [ ] `app/models/fitness_model.py` — all model methods
- [ ] `app/routes/fitness.py` — rewrite with full route set

## Templates
- [ ] `app/templates/fitness_index.html` — today's workout + body weight + inline set logging
- [ ] `app/templates/fitness_settings.html` — program management, day-by-day exercise editor
- [ ] `app/templates/fitness_log.html` — workout history with sets

## Static
- [ ] `app/static/css/fitness.css` — rewrite mobile-first
- [ ] `app/static/js/fitness.js` — AJAX set logging

## Verify
- [ ] Run app, visit fitness index, log a set
- [ ] Verify body weight saves
- [ ] Verify settings page shows exercises per day, add/remove works
- [ ] Verify log history shows sets
