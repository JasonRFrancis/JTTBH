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

from datetime import date, datetime

from flask import (
    Blueprint,
    render_template,
    session,
    jsonify,
    current_app,
)

from app.services.database import db_manager
from app.services.decorators import (
    login_required,
    permission_required_read,
    PERM_DASHBOARD,
    PERM_HABIT,
    PERM_TODO,
)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

dashboard_bp = Blueprint('dashboard', __name__)


# ---------------------------------------------------------------------------
# Day-of-week bitmask helper
# ---------------------------------------------------------------------------

# Python weekday(): Monday=0 … Sunday=6
# Map to bit positions matching the habit.dayweek column:
#   Monday=1, Tuesday=2, Wednesday=4, Thursday=8,
#   Friday=16, Saturday=32, Sunday=64
_DOW_BITS = {
    0: 1,    # Monday
    1: 2,    # Tuesday
    2: 4,    # Wednesday
    3: 8,    # Thursday
    4: 16,   # Friday
    5: 32,   # Saturday
    6: 64,   # Sunday
}


def _today_dow_bit() -> int:
    """Return the bitmask value for today's day of the week."""
    return _DOW_BITS[date.today().weekday()]


# ---------------------------------------------------------------------------
# Data-gathering helpers
# ---------------------------------------------------------------------------

def _get_today_habits(user_id: str) -> list[dict]:
    """
    Return today's active habits for *user_id*.

    Only habits whose ``dayweek`` bitmask includes today are returned.
    For each habit the most recent habit_entry for today is joined so the
    template knows whether the habit has been completed.
    """
    today     = date.today().isoformat()
    dow_bit   = _today_dow_bit()

    rows = db_manager.execute_query(
        """
        SELECT
            h.habitID,
            h.name,
            h.icon,
            h.position,
            h.dayweek,
            (
                SELECT he.completed
                FROM habit_entry he
                WHERE he.habitID = h.habitID
                  AND he.entry   = %s
                ORDER BY he.id DESC
                LIMIT 1
            ) AS completed
        FROM habit h
        WHERE h.userID = %s
          AND h.id = (
              SELECT MAX(h2.id)
              FROM habit h2
              WHERE h2.habitID = h.habitID
          )
          AND h.name   IS NOT NULL
          AND h.active = 1
          AND (h.dayweek & %s)
        ORDER BY h.position
        """,
        (today, user_id, dow_bit),
    )
    # Normalise completed to bool
    for row in rows:
        row['completed'] = bool(row.get('completed'))
    return rows


def _get_today_todos(user_id: str) -> list[dict]:
    """
    Return today's daily todos for *user_id*.
    """
    today = date.today().isoformat()

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
        'today':  date.today().isoformat(),
        'habits': [],
        'todos':  [],
    }

    if perm_read & PERM_HABIT:
        try:
            data['habits'] = _get_today_habits(user_id)
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
        habits=data['habits'],
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
