"""
JTTBH Fitness Model
===================
All database interactions for the fitness feature.

Tables
------
fitness           — user workout programs (insert-only; name IS NULL = soft-deleted)
fitness_exercise  — shared exercise catalog (reference data; direct UPDATE allowed)
fitness_program   — exercises scheduled per day within a program (insert-only;
                    exerciseID IS NULL = soft-deleted)
fitness_log       — workout sessions (insert-only; log_date IS NULL = soft-deleted)
fitness_logSet    — individual sets within a session (insert-only;
                    exerciseID IS NULL = soft-deleted)
fitness_bodyWeight — body-weight readings, one per date per user

day_of_week convention: 0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday,
                        4=Thursday, 5=Friday, 6=Saturday
(same as: (python_date.weekday() + 1) % 7)
"""

import uuid
from datetime import date, datetime

from app.services.database import db_manager

DAY_NAMES = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday',
             4: 'Thursday', 5: 'Friday', 6: 'Saturday'}


class FitnessModel:

    # ------------------------------------------------------------------ #
    # Programs                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_active_program(user_id: str) -> dict | None:
        return db_manager.execute_one("""
            SELECT f.fitnessID, f.name, f.description, f.start_date, f.active
            FROM fitness f
            WHERE f.userID = %s
              AND f.name IS NOT NULL
              AND f.active = 1
              AND f.id = (SELECT MAX(f2.id) FROM fitness f2 WHERE f2.fitnessID = f.fitnessID)
            ORDER BY f.id DESC
            LIMIT 1
        """, (user_id,))

    @staticmethod
    def get_programs(user_id: str) -> list[dict]:
        return db_manager.execute_query("""
            SELECT f.fitnessID, f.name, f.description, f.start_date, f.active
            FROM fitness f
            WHERE f.userID = %s
              AND f.name IS NOT NULL
              AND f.id = (SELECT MAX(f2.id) FROM fitness f2 WHERE f2.fitnessID = f.fitnessID)
            ORDER BY f.active DESC, f.id DESC
        """, (user_id,))

    @staticmethod
    def create_program(user_id: str, name: str, description: str) -> str:
        fitness_id = str(uuid.uuid4())
        db_manager.execute_insert("""
            INSERT INTO fitness (fitnessID, userID, name, description, active, created, created_by)
            VALUES (%s, %s, %s, %s, 0, NOW(), %s)
        """, (fitness_id, user_id, name, description or None, user_id))
        return fitness_id

    @staticmethod
    def activate_program(user_id: str, fitness_id: str) -> None:
        """Deactivate all programs for this user, then activate the target."""
        active = db_manager.execute_query("""
            SELECT f.fitnessID, f.name, f.description, f.start_date
            FROM fitness f
            WHERE f.userID = %s
              AND f.active = 1
              AND f.name IS NOT NULL
              AND f.id = (SELECT MAX(f2.id) FROM fitness f2 WHERE f2.fitnessID = f.fitnessID)
        """, (user_id,))
        for prog in active:
            if prog['fitnessID'] != fitness_id:
                db_manager.execute_insert("""
                    INSERT INTO fitness (fitnessID, userID, name, description, active, created, created_by)
                    SELECT fitnessID, userID, name, description, 0, NOW(), %s
                    FROM fitness
                    WHERE fitnessID = %s
                      AND id = (SELECT MAX(id) FROM fitness WHERE fitnessID = %s)
                """, (user_id, prog['fitnessID'], prog['fitnessID']))
        # Activate the target
        db_manager.execute_insert("""
            INSERT INTO fitness (fitnessID, userID, name, description, active, created, created_by)
            SELECT fitnessID, userID, name, description, 1, NOW(), %s
            FROM fitness
            WHERE fitnessID = %s
              AND id = (SELECT MAX(id) FROM fitness WHERE fitnessID = %s)
        """, (user_id, fitness_id, fitness_id))

    @staticmethod
    def delete_program(fitness_id: str, user_id: str) -> None:
        db_manager.execute_insert("""
            INSERT INTO fitness (fitnessID, userID, name, description, active, created, created_by)
            SELECT fitnessID, userID, NULL, description, 0, NOW(), %s
            FROM fitness
            WHERE fitnessID = %s
              AND id = (SELECT MAX(id) FROM fitness WHERE fitnessID = %s)
        """, (user_id, fitness_id, fitness_id))

    # ------------------------------------------------------------------ #
    # Program exercises                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_program_schedule(fitness_id: str) -> dict[int, list[dict]]:
        """Return all exercises grouped by day_of_week."""
        rows = db_manager.execute_query("""
            SELECT fp.programID, fp.day_of_week, fp.order_index,
                   fp.recommended_sets, fp.recommended_reps, fp.recommended_weight,
                   fp.recommended_duration, fp.recommended_speed, fp.recommended_incline,
                   fp.notes, fp.location,
                   fe.exerciseID, fe.name AS exercise_name, fe.type AS exercise_type,
                   fe.muscle_group, fe.equipment_type, fe.video_url
            FROM fitness_program fp
            JOIN fitness_exercise fe ON fe.exerciseID = fp.exerciseID
            WHERE fp.fitnessID = %s
              AND fp.exerciseID IS NOT NULL
            ORDER BY fp.day_of_week, fp.order_index
        """, (fitness_id,))
        schedule = {d: [] for d in range(7)}
        for row in rows:
            schedule[row['day_of_week']].append(row)
        return schedule

    @staticmethod
    def get_day_exercises(fitness_id: str, day_of_week: int) -> list[dict]:
        return db_manager.execute_query("""
            SELECT fp.programID, fp.order_index,
                   fp.recommended_sets, fp.recommended_reps, fp.recommended_weight,
                   fp.recommended_duration, fp.recommended_speed, fp.recommended_incline,
                   fp.notes, fp.location,
                   fe.exerciseID, fe.name AS exercise_name, fe.type AS exercise_type,
                   fe.muscle_group, fe.equipment_type, fe.video_url
            FROM fitness_program fp
            JOIN fitness_exercise fe ON fe.exerciseID = fp.exerciseID
            WHERE fp.fitnessID = %s
              AND fp.day_of_week = %s
              AND fp.exerciseID IS NOT NULL
            ORDER BY fp.order_index
        """, (fitness_id, day_of_week))

    @staticmethod
    def add_program_exercise(
        fitness_id: str,
        day_of_week: int,
        exercise_id: str,
        location: str,
        sets: int | None,
        reps: int | None,
        weight: float | None,
        notes: str | None,
        order_index: int,
        duration: int | None,
        speed: float | None,
        incline: float | None,
    ) -> str:
        program_id = str(uuid.uuid4())
        db_manager.execute_insert("""
            INSERT INTO fitness_program
              (programID, fitnessID, day_of_week, exerciseID, order_index,
               recommended_sets, recommended_reps, recommended_weight,
               notes, location, recommended_duration, recommended_speed,
               recommended_incline, created)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (program_id, fitness_id, day_of_week, exercise_id, order_index,
              sets, reps, weight, notes or None, location,
              duration, speed, incline))
        return program_id

    @staticmethod
    def update_program_exercise(
        program_id: str,
        sets: int | None,
        reps: int | None,
        weight: float | None,
        notes: str | None,
        location: str,
        duration: int | None,
        speed: float | None,
        incline: float | None,
    ) -> None:
        db_manager.execute_insert("""
            INSERT INTO fitness_program
              (programID, fitnessID, day_of_week, exerciseID, order_index,
               recommended_sets, recommended_reps, recommended_weight,
               notes, location, recommended_duration, recommended_speed,
               recommended_incline, created)
            SELECT programID, fitnessID, day_of_week, exerciseID, order_index,
                   %s, %s, %s, %s, %s, %s, %s, %s, NOW()
            FROM fitness_program
            WHERE programID = %s
              AND id = (SELECT MAX(id) FROM fitness_program WHERE programID = %s)
        """, (sets, reps, weight, notes, location, duration, speed, incline,
              program_id, program_id))

    @staticmethod
    def delete_program_exercise(program_id: str, user_id: str) -> None:
        db_manager.execute_insert("""
            INSERT INTO fitness_program
              (programID, fitnessID, day_of_week, exerciseID, order_index,
               recommended_sets, recommended_reps, recommended_weight,
               notes, location, created)
            SELECT programID, fitnessID, day_of_week, NULL, order_index,
                   recommended_sets, recommended_reps, recommended_weight,
                   notes, location, NOW()
            FROM fitness_program
            WHERE programID = %s
              AND id = (SELECT MAX(id) FROM fitness_program WHERE programID = %s)
        """, (program_id, program_id))

    # ------------------------------------------------------------------ #
    # Exercise catalog                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_exercise(
        name: str,
        description: str | None,
        equipment_type: str | None,
        exercise_type: str,
        muscle_group: str | None,
    ) -> str:
        exercise_id = str(uuid.uuid4())
        db_manager.execute_insert("""
            INSERT INTO fitness_exercise
              (exerciseID, name, description, equipment_type, type, muscle_group,
               video_url, created, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, NULL, NOW(), NULL)
        """, (exercise_id, name, description or None, equipment_type or None,
              exercise_type, muscle_group or None))
        return exercise_id

    @staticmethod
    def get_exercise_catalog() -> list[dict]:
        return db_manager.execute_query("""
            SELECT exerciseID, name, type AS exercise_type, equipment_type, muscle_group, video_url
            FROM fitness_exercise
            WHERE name IS NOT NULL
            ORDER BY muscle_group, name
        """, ())

    # ------------------------------------------------------------------ #
    # Workout logs                                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_todays_log(user_id: str, log_date: date) -> dict | None:
        return db_manager.execute_one("""
            SELECT fl.logID, fl.fitnessID, fl.log_date,
                   fl.start_time, fl.end_time, fl.location, fl.notes
            FROM fitness_log fl
            WHERE fl.userID = %s
              AND fl.log_date = %s
              AND fl.log_date IS NOT NULL
              AND fl.id = (SELECT MAX(fl2.id) FROM fitness_log fl2 WHERE fl2.logID = fl.logID)
            ORDER BY fl.id DESC
            LIMIT 1
        """, (user_id, log_date))

    @staticmethod
    def get_or_create_log(user_id: str, fitness_id: str | None, log_date: date) -> str:
        existing = FitnessModel.get_todays_log(user_id, log_date)
        if existing:
            return existing['logID']
        log_id = str(uuid.uuid4())
        db_manager.execute_insert("""
            INSERT INTO fitness_log
              (logID, userID, fitnessID, log_date, start_time, location, created)
            VALUES (%s, %s, %s, %s, NOW(), 'gym', NOW())
        """, (log_id, user_id, fitness_id, log_date))
        return log_id

    @staticmethod
    def end_workout(log_id: str) -> None:
        db_manager.execute_insert("""
            INSERT INTO fitness_log
              (logID, userID, fitnessID, log_date, start_time, end_time, location, notes, created)
            SELECT logID, userID, fitnessID, log_date, start_time, NOW(), location, notes, NOW()
            FROM fitness_log
            WHERE logID = %s
              AND id = (SELECT MAX(id) FROM fitness_log WHERE logID = %s)
        """, (log_id, log_id))

    @staticmethod
    def get_recent_logs(user_id: str, limit: int = 60) -> list[dict]:
        return db_manager.execute_query("""
            SELECT fl.logID, fl.log_date, fl.start_time, fl.end_time,
                   fl.location, fl.notes, f.name AS program_name
            FROM fitness_log fl
            LEFT JOIN fitness f ON f.fitnessID = fl.fitnessID
            WHERE fl.userID = %s
              AND fl.log_date IS NOT NULL
              AND fl.id = (SELECT MAX(fl2.id) FROM fitness_log fl2 WHERE fl2.logID = fl.logID)
            ORDER BY fl.log_date DESC
            LIMIT %s
        """, (user_id, limit))

    # ------------------------------------------------------------------ #
    # Sets                                                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_log_sets(log_id: str) -> list[dict]:
        """Current (non-deleted) sets for a workout session, grouped by exercise."""
        return db_manager.execute_query("""
            SELECT ls.logSetID, ls.exerciseID, ls.set_number,
                   ls.actual_weight, ls.actual_reps, ls.notes,
                   ls.duration_minutes, ls.speed, ls.incline,
                   fe.name AS exercise_name, fe.type AS exercise_type
            FROM fitness_logSet ls
            JOIN fitness_exercise fe ON fe.exerciseID = ls.exerciseID
            WHERE ls.logID = %s
              AND ls.exerciseID IS NOT NULL
              AND ls.id = (SELECT MAX(ls2.id) FROM fitness_logSet ls2
                           WHERE ls2.logSetID = ls.logSetID)
            ORDER BY ls.exerciseID, ls.set_number
        """, (log_id,))

    @staticmethod
    def log_set(
        log_id: str,
        exercise_id: str,
        set_number: int,
        weight: float | None,
        reps: int | None,
        notes: str | None,
        duration: int | None,
        speed: float | None,
        incline: float | None,
    ) -> str:
        log_set_id = str(uuid.uuid4())
        db_manager.execute_insert("""
            INSERT INTO fitness_logSet
              (logSetID, logID, exerciseID, set_number,
               actual_weight, actual_reps, notes,
               duration_minutes, speed, incline, created)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (log_set_id, log_id, exercise_id, set_number,
              weight, reps, notes or None, duration, speed, incline))
        return log_set_id

    @staticmethod
    def delete_log_set(log_set_id: str) -> None:
        db_manager.execute_insert("""
            INSERT INTO fitness_logSet
              (logSetID, logID, exerciseID, set_number,
               actual_weight, actual_reps, notes,
               duration_minutes, speed, incline, created)
            SELECT logSetID, logID, NULL, set_number,
                   actual_weight, actual_reps, notes,
                   duration_minutes, speed, incline, NOW()
            FROM fitness_logSet
            WHERE logSetID = %s
              AND id = (SELECT MAX(id) FROM fitness_logSet WHERE logSetID = %s)
        """, (log_set_id, log_set_id))

    @staticmethod
    def get_last_sets_for_exercise(user_id: str, exercise_id: str, before_date: date) -> list[dict]:
        """All sets from the most recent session for this exercise, before today."""
        return db_manager.execute_query("""
            SELECT ls.set_number, ls.actual_weight, ls.actual_reps,
                   ls.duration_minutes, ls.speed, ls.incline
            FROM fitness_logSet ls
            JOIN fitness_log fl ON fl.logID = ls.logID
            WHERE fl.userID = %s
              AND ls.exerciseID = %s
              AND fl.log_date < %s
              AND fl.log_date IS NOT NULL
              AND ls.exerciseID IS NOT NULL
              AND ls.id = (SELECT MAX(ls2.id) FROM fitness_logSet ls2
                           WHERE ls2.logSetID = ls.logSetID)
              AND fl.log_date = (
                  SELECT MAX(fl2.log_date)
                  FROM fitness_log fl2
                  JOIN fitness_logSet ls2 ON ls2.logID = fl2.logID
                  WHERE fl2.userID = %s
                    AND ls2.exerciseID = %s
                    AND fl2.log_date < %s
                    AND fl2.log_date IS NOT NULL
                    AND ls2.exerciseID IS NOT NULL
              )
            ORDER BY ls.set_number
        """, (user_id, exercise_id, before_date, user_id, exercise_id, before_date))

    # ------------------------------------------------------------------ #
    # Body weight                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_todays_body_weight(user_id: str, recorded: date) -> dict | None:
        return db_manager.execute_one("""
            SELECT weightID, weight, unit, recorded
            FROM fitness_bodyWeight
            WHERE userID = %s AND recorded = %s
            ORDER BY id DESC
            LIMIT 1
        """, (user_id, recorded))

    @staticmethod
    def log_body_weight(user_id: str, weight: float, recorded: date) -> str:
        weight_id = str(uuid.uuid4())
        db_manager.execute_insert("""
            INSERT INTO fitness_bodyWeight
              (weightID, userID, weight, unit, recorded, created, created_by)
            VALUES (%s, %s, %s, 'lbs', %s, NOW(), %s)
        """, (weight_id, user_id, weight, recorded, user_id))
        return weight_id

    @staticmethod
    def get_weight_history(user_id: str, limit: int = 90) -> list[dict]:
        return db_manager.execute_query("""
            SELECT bw.weightID, bw.weight, bw.unit, bw.recorded
            FROM fitness_bodyWeight bw
            WHERE bw.userID = %s
              AND bw.id = (SELECT MAX(bw2.id) FROM fitness_bodyWeight bw2
                           WHERE bw2.userID = bw.userID AND bw2.recorded = bw.recorded)
            ORDER BY bw.recorded DESC
            LIMIT %s
        """, (user_id, limit))
