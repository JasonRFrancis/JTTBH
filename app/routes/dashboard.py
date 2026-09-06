"""
JTTBH Dashboard Routes
========================
The dashboard aggregates widgets from multiple features into a single overview
page.  It is the default landing page for authenticated users.

Routes
------
GET /<username>/dashboard/index       – HTML dashboard page.
GET /<username>/dashboard/index/json  – JSON snapshot of dashboard data.

Data collected
--------------
- Today's habits (filtered to the current day-of-week bitmask).
- Today's daily todos (due today, list_type='daily').

Permissions
-----------
Requires ``PERM_DASHBOARD`` read access.
"""

from datetime import date, timedelta

from app.services.timezone_utils import user_today

from flask import (
    Blueprint,
    render_template,
    session,
    jsonify,
    current_app,
)

from app.services.decorators import (
    login_required,
    permission_required_read,
    PERM_DASHBOARD,
    PERM_HABIT,
    PERM_TODO,
    PERM_FITNESS,
    PERM_STUDY,
)
from app.models.habit_model import HabitModel
from app.models.fitness_model import FitnessModel
from app.models.study_model import StudyModel
from app.services.database import db_manager


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

dashboard_bp = Blueprint('dashboard', __name__)


# ---------------------------------------------------------------------------
# Data-gathering helpers
# ---------------------------------------------------------------------------

def _get_today_habit_grid(user_id: str) -> tuple[list[dict], int, int]:
    """Return (grid, completed_count, total_count) for today."""
    grid = HabitModel.get_grid_with_streaks(user_id, user_today())
    completed, total = HabitModel.grid_stats(grid)
    return grid, completed, total


def _get_prev_day_habit_grid(user_id: str) -> tuple[list[dict], int, date]:
    """Return (grid, unresolved_count, date) for yesterday.

    A cell is "unresolved" when the habit applies that day but has no explicit
    complete/not-completed answer (completed is None). The dashboard only shows
    the catch-up grid while unresolved_count > 0.
    """
    yesterday = user_today() - timedelta(days=1)
    grid = HabitModel.get_grid_for_date(user_id, yesterday)
    unresolved = sum(
        1 for c in grid
        if c['habitID'] and c['applies'] and c['completed'] is None
    )
    return grid, unresolved, yesterday


def _get_today_todos(user_id: str) -> list[dict]:
    """
    Return today's daily todos for *user_id*.
    """
    today = user_today().isoformat()

    rows = db_manager.execute_query(
        """
        SELECT
            t.todoID,
            t.title,
            t.completed,
            t.position,
            t.content
        FROM todo t
        WHERE t.userID    = %s
          AND t.due       = %s
          AND t.list_type = 'daily'
          AND t.id = (
              SELECT MAX(t2.id)
              FROM todo t2
              WHERE t2.todoID = t.todoID
          )
          AND t.title IS NOT NULL
        ORDER BY t.position, t.created
        """,
        (user_id, today),
    )
    for row in rows:
        row['completed'] = bool(row.get('completed'))
    return rows


def _get_fitness_summary(user_id: str) -> dict:
    program = FitnessModel.get_active_program(user_id)
    if not program:
        return {'program': None, 'exercise_count': 0, 'exercises': []}
    today = user_today()
    dow = (today.weekday() + 1) % 7
    exercises = FitnessModel.get_day_exercises(program['fitnessID'], dow)
    return {'program': program, 'exercise_count': len(exercises), 'exercises': exercises}


def _get_study_summary(user_id: str) -> dict:
    today = user_today()
    subs = StudyModel.get_user_subscriptions(user_id)
    completions = StudyModel.get_completions_for_date(user_id, today)
    items = []
    for sub in subs:
        sources = StudyModel.get_sources(sub['collectionID'])
        for item in StudyModel.sources_for_date(sub, sources, today, user_id):
            items.append({**item, 'completed': item['sourceID'] in completions})
    streak = StudyModel.calculate_streak(user_id, today)
    return {'total': len(items), 'completed': len(completions), 'sources': items, 'streak': streak}


def _gather_dashboard_data(user_id: str, perm_read: int) -> dict:
    """
    Collect all dashboard widget data, gating each query behind the
    appropriate permission bit so the dashboard degrades gracefully for
    users who lack certain feature access.
    """
    data: dict = {
        'today':                 user_today(),
        'habit_today':           [],
        'habit_completed':       0,
        'habit_total':           0,
        'prev_habit_grid':       [],
        'prev_habit_unresolved': 0,
        'prev_habit_date':       None,
        'todos':                 [],
        'fitness':               None,
        'study':                 None,
    }

    if perm_read & PERM_HABIT:
        try:
            grid, completed, total = _get_today_habit_grid(user_id)
            # Dashboard shows today's habits as a to-do list: only the ones
            # still to be done. Completed habits drop off on the next load.
            data['habit_today'] = [
                c for c in grid
                if c['habitID'] and c['applies'] and c['completed'] != 1
            ]
            data['habit_completed'] = completed
            data['habit_total']     = total
        except Exception as exc:
            current_app.logger.warning('Dashboard: failed to load habits: %s', exc)

        try:
            prev_grid, unresolved, prev_date = _get_prev_day_habit_grid(user_id)
            if unresolved > 0:
                data['prev_habit_grid']       = prev_grid
                data['prev_habit_unresolved'] = unresolved
                data['prev_habit_date']       = prev_date
        except Exception as exc:
            current_app.logger.warning('Dashboard: failed to load previous-day habits: %s', exc)

    if perm_read & PERM_TODO:
        try:
            data['todos'] = _get_today_todos(user_id)
        except Exception as exc:
            current_app.logger.warning('Dashboard: failed to load todos: %s', exc)

    if perm_read & PERM_FITNESS:
        try:
            data['fitness'] = _get_fitness_summary(user_id)
        except Exception as exc:
            current_app.logger.warning('Dashboard: failed to load fitness: %s', exc)

    if perm_read & PERM_STUDY:
        try:
            data['study'] = _get_study_summary(user_id)
        except Exception as exc:
            current_app.logger.warning('Dashboard: failed to load study: %s', exc)

    return data


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@dashboard_bp.route('/index')
@login_required
@permission_required_read(PERM_DASHBOARD)
def index(username: str):
    """Render the main dashboard page."""
    user_id   = session['user_id']
    perm_read = session.get('perm_read', 0)

    data = _gather_dashboard_data(user_id, perm_read)

    return render_template(
        'dashboard_index.html',
        username=username,
        area='dashboard',
        today=data['today'],
        habit_today=data['habit_today'],
        habit_completed=data['habit_completed'],
        habit_total=data['habit_total'],
        prev_habit_grid=data['prev_habit_grid'],
        prev_habit_unresolved=data['prev_habit_unresolved'],
        prev_habit_date=data['prev_habit_date'],
        todos=data['todos'],
        fitness=data['fitness'],
        study=data['study'],
    )


@dashboard_bp.route('/index/json')
@login_required
@permission_required_read(PERM_DASHBOARD)
def index_json(username: str):
    """Return dashboard data as JSON for client-side refresh."""
    user_id   = session['user_id']
    perm_read = session.get('perm_read', 0)

    data = _gather_dashboard_data(user_id, perm_read)
    data['today'] = data['today'].isoformat()
    if data['prev_habit_date'] is not None:
        data['prev_habit_date'] = data['prev_habit_date'].isoformat()
    return jsonify(data)
