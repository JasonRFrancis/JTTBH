"""
JTTBH User Routes
===================
Routes for the authenticated user's own settings area.

Routes
------
GET  /<username>/settings
    Render the user settings page showing preferences and vacation periods.
    Vacation add/delete forms submit to the vacation blueprint routes.

POST /<username>/settings/post
    Upsert a single key-value preference in the ``user_preference`` table.

Preferences
-----------
Stored as individual key-value rows in ``user_preference``.  Supported keys:
    todo_list1_name  – Display name for custom to-do list 1
    todo_list2_name  – Display name for custom to-do list 2
    todo_list3_name  – Display name for custom to-do list 3
    todo_list4_name  – Display name for custom to-do list 4

Design
------
All POST routes follow the PRG pattern: they perform the mutation, flash a
message, and redirect to the GET settings page.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
)

from app.services.database import db_manager
from app.services.decorators import login_required


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

user_bp = Blueprint('user', __name__)


# ---------------------------------------------------------------------------
# Preference keys allowed from form submissions (allowlist)
# ---------------------------------------------------------------------------

ALLOWED_PREF_KEYS = {
    'todo_list1_name',
    'todo_list2_name',
    'todo_list3_name',
    'todo_list4_name',
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_preferences(user_id: str) -> dict[str, str]:
    """
    Return all preferences for *user_id* as a plain dict.

    When a preference key has multiple rows (historical entries), only the
    most recent value (highest ``id``) is used.
    """
    rows = db_manager.execute_query(
        """
        SELECT preference, value
        FROM user_preference
        WHERE userID = %s
        ORDER BY id DESC
        """,
        (user_id,),
    )
    prefs: dict[str, str] = {}
    for row in rows:
        key = row['preference']
        if key and key not in prefs:   # keep only the most recent
            prefs[key] = row['value'] or ''
    return prefs


def _load_vacations(user_id: str) -> list[dict]:
    """Return all vacation periods, most recent first."""
    return db_manager.execute_query(
        """
        SELECT vacationID, name, `start`, `end`, description
        FROM vacation
        WHERE userID = %s
        ORDER BY `start` DESC
        """,
        (user_id,),
    )


def _upsert_preference(user_id: str, key: str, value: str) -> None:
    """
    Insert a new preference row (append-only history).

    The application always reads the most-recent row, so inserting a new row
    effectively replaces the value while preserving the audit trail.
    """
    db_manager.execute_insert(
        """
        INSERT INTO user_preference (userID, preference, value, created, created_by)
        VALUES (%s, %s, %s, NOW(), %s)
        """,
        (user_id, key, value, user_id),
    )


# ---------------------------------------------------------------------------
# Routes – GET
# ---------------------------------------------------------------------------

@user_bp.route('/settings')
@login_required
def settings(username: str):
    """Render the user settings page."""
    user_id = session['user_id']
    prefs   = _load_preferences(user_id)
    vacs    = _load_vacations(user_id)
    return render_template(
        'user_settings.html',
        username=username,
        area='settings',
        prefs=prefs,
        vacations=vacs,
    )


# ---------------------------------------------------------------------------
# Routes – POST
# ---------------------------------------------------------------------------

@user_bp.route('/settings/post', methods=['POST'])
@login_required
def save_setting(username: str):
    """
    Upsert a single user preference.

    Form data
    ---------
    key   – One of the ALLOWED_PREF_KEYS.
    value – The new value (max 100 chars).
    """
    user_id = session['user_id']
    key     = request.form.get('key', '').strip()
    value   = request.form.get('value', '').strip()[:100]

    if key not in ALLOWED_PREF_KEYS:
        flash('Unknown preference key.', 'error')
        return redirect(url_for('user.settings', username=username))

    _upsert_preference(user_id, key, value)
    flash('Setting saved.', 'success')
    return redirect(url_for('user.settings', username=username))


