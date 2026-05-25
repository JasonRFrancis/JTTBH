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

from datetime import date

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
)
from app.models.habit_model import HabitModel


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

dashboard_bp = Blueprint('dashboard', __name__)


# ---------------------------------------------------------------------------
# Data-gathering helpers
# ---------------------------------------------------------------------------

def _get_today_habit_grid(user_id: str) -> tuple[list[dict], int, int]:
    """
    Return (grid, completed_count, total_count) for today.

    grid is the 25-element list from HabitModel.get_grid_for_date, with
    streak attached to each cell that has a habit.
    """
    today   = user_today()
    grid    = HabitModel.get_grid_for_date(user_id, today)
    streaks = HabitModel.calculate_streaks(user_id)
    for cell in grid:
        if cell['habitID']:
            cell['streak'] = streaks.get(cell['habitID'], 0)
    total     = sum(1 for c in grid if c['habitID'] and c['applies'])
    completed = sum(1 for c in grid if c['habitID'] and c['applies'] and c['completed'] == 1)
    return grid, completed, total


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


def _gather_dashboard_data(user_id: str, perm_read: int) -> dict:
    """
    Collect all dashboard widget data, gating each query behind the
    appropriate permission bit so the dashboard degrades gracefully for
    users who lack certain feature access.
    """
    data: dict = {
        'today':           user_today().isoformat(),
        'habit_grid':      [],
        'habit_completed': 0,
        'habit_total':     0,
        'todos':           [],
    }

    if perm_read & PERM_HABIT:
        try:
            grid, completed, total = _get_today_habit_grid(user_id)
            data['habit_grid']      = grid
            data['habit_completed'] = completed
            data['habit_total']     = total
        except Exception as exc:
            current_app.logger.warning('Dashboard: failed to load habits: %s', exc)

    if perm_read & PERM_TODO:
        try:
            data['todos'] = _get_today_todos(user_id)
        except Exception as exc:
            current_app.logger.warning('Dashboard: failed to load todos: %s', exc)

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
        habit_grid=data['habit_grid'],
        habit_completed=data['habit_completed'],
        habit_total=data['habit_total'],
        todos=data['todos'],
    )


@dashboard_bp.route('/index/json')
@login_required
@permission_required_read(PERM_DASHBOARD)
def index_json(username: str):
    """Return dashboard data as JSON for client-side refresh."""
    user_id   = session['user_id']
    perm_read = session.get('perm_read', 0)

    data = _gather_dashboard_data(user_id, perm_read)
    return jsonify(data)
