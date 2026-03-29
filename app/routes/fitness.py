"""
Fitness Routes
==============
Flask blueprint for the fitness / workout tracking feature.

URL patterns
------------
GET  /<username>/fitness/index     -> today's scheduled exercises
GET  /<username>/fitness/log       -> workout log history

All write routes (log a workout, add a set, etc.) are stubs pending full
implementation of the fitness program builder.
"""

from datetime import date, datetime

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.services.database import db_manager
from app.services.decorators import (
    PERM_FITNESS,
    login_required,
    permission_required_read,
    permission_required_write,
)

fitness_bp = Blueprint('fitness', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_active_program(user_id: str) -> dict | None:
    """Return the user's current active fitness program, if any."""
    return db_manager.execute_one(
        """
        SELECT f.fitnessID, f.name, f.description, f.start_date
        FROM fitness f
        WHERE f.userID = %s
          AND f.active = 1
          AND f.name IS NOT NULL
        ORDER BY f.id DESC
        LIMIT 1
        """,
        (user_id,),
    )


def _get_todays_exercises(fitness_id: str, day_of_week: int) -> list[dict]:
    """Return scheduled exercises for the given day of week in a program."""
    return db_manager.execute_query(
        """
        SELECT fp.programID, fp.exerciseID, fp.order_index,
               fp.recommended_sets, fp.recommended_reps, fp.recommended_weight,
               fp.rest_seconds, fp.notes,
               fe.name AS exercise_name, fe.equipment_type, fe.muscle_group, fe.video_url
        FROM fitness_program fp
        JOIN fitness_exercise fe ON fe.exerciseID = fp.exerciseID
        WHERE fp.fitnessID = %s
          AND fp.day_of_week = %s
          AND fp.exerciseID IS NOT NULL
        ORDER BY fp.order_index
        """,
        (fitness_id, day_of_week),
    )


def _get_todays_log(user_id: str, log_date: date) -> dict | None:
    """Return the most recent workout log entry for today."""
    return db_manager.execute_one(
        """
        SELECT fl.logID, fl.fitnessID, fl.log_date, fl.start_time, fl.end_time,
               fl.location, fl.notes
        FROM fitness_log fl
        WHERE fl.userID = %s
          AND fl.log_date = %s
          AND fl.log_date IS NOT NULL
        ORDER BY fl.id DESC
        LIMIT 1
        """,
        (user_id, log_date),
    )


def _get_recent_logs(user_id: str, limit: int = 30) -> list[dict]:
    """Return the N most recent workout log entries."""
    return db_manager.execute_query(
        """
        SELECT fl.logID, fl.log_date, fl.start_time, fl.end_time,
               fl.location, fl.notes, f.name AS program_name
        FROM fitness_log fl
        LEFT JOIN fitness f ON f.fitnessID = fl.fitnessID
        WHERE fl.userID = %s
          AND fl.log_date IS NOT NULL
        ORDER BY fl.log_date DESC
        LIMIT %s
        """,
        (user_id, limit),
    )


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@fitness_bp.route('/index')
@login_required
@permission_required_read(PERM_FITNESS)
def index(username: str):
    """
    Display today's scheduled workout based on the active program.

    Shows scheduled exercises for today's day of week, plus today's log
    entry if a workout has already been recorded.
    """
    user_id = session['user_id']
    today = date.today()
    # Python weekday(): Monday=0, Sunday=6. Fitness schema: 0=Sunday, 1=Monday, ..., 6=Saturday.
    day_of_week = (today.weekday() + 1) % 7

    program = _get_active_program(user_id)
    exercises = []
    if program:
        exercises = _get_todays_exercises(program['fitnessID'], day_of_week)

    todays_log = _get_todays_log(user_id, today)

    return render_template(
        'fitness_index.html',
        program=program,
        exercises=exercises,
        todays_log=todays_log,
        today=today,
        day_of_week=day_of_week,
        username=username,
    )


@fitness_bp.route('/log')
@login_required
@permission_required_read(PERM_FITNESS)
def log(username: str):
    """
    Display the workout log history.
    """
    user_id = session['user_id']
    logs = _get_recent_logs(user_id)

    return render_template(
        'fitness_log.html',
        logs=logs,
        username=username,
    )
