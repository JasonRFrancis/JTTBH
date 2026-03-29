"""
Vacation Routes
===============
Flask blueprint for vacation period management.

URL patterns
------------
GET  /<username>/vacation/index            -> calendar view of vacation periods
POST /<username>/vacation/create/post      -> add a vacation period
POST /<username>/vacation/delete/post/<vacationID>  -> delete a vacation period
"""

import uuid
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
    login_required,
    permission_required_read,
    permission_required_write,
    PERM_HABIT,
)

vacation_bp = Blueprint('vacation', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _redirect_to_index(username: str):
    return redirect(url_for('vacation.index', username=username))


def _get_vacations(user_id: str) -> list[dict]:
    """Return all vacation periods for a user, ordered by start date."""
    return db_manager.execute_query(
        """
        SELECT vacationID, userID, start, end, name, description, created
        FROM vacation
        WHERE userID = %s
        ORDER BY start DESC
        """,
        (user_id,),
    )


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@vacation_bp.route('/index')
@login_required
@permission_required_read(PERM_HABIT)
def index(username: str):
    """
    List all vacation periods for the user.

    Template context
    ----------------
    vacations : list[dict]   All vacation periods, newest start date first.
    today     : date
    username  : str
    """
    user_id = session['user_id']
    vacations = _get_vacations(user_id)

    return render_template(
        'vacation_index.html',
        vacations=vacations,
        today=date.today(),
        username=username,
    )


# ---------------------------------------------------------------------------
# POST routes (PRG pattern)
# ---------------------------------------------------------------------------

@vacation_bp.route('/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_HABIT)
@permission_required_write(PERM_HABIT)
def create(username: str):
    """
    Add a vacation period.

    Form fields
    -----------
    name        : str   Required. Short name for the vacation.
    start       : str   Required. ISO date (YYYY-MM-DD) start date.
    end         : str   Required. ISO date (YYYY-MM-DD) end date.
    description : str   Optional.
    """
    user_id = session['user_id']
    name = request.form.get('name', '').strip()
    start_str = request.form.get('start', '').strip()
    end_str = request.form.get('end', '').strip()
    description = request.form.get('description', '').strip() or None

    if not name:
        flash('Vacation name is required.', 'error')
        return _redirect_to_index(username)

    try:
        start = datetime.strptime(start_str, '%Y-%m-%d').date()
        end = datetime.strptime(end_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('Valid start and end dates are required (YYYY-MM-DD).', 'error')
        return _redirect_to_index(username)

    if end < start:
        flash('End date must be on or after start date.', 'error')
        return _redirect_to_index(username)

    vacation_id = str(uuid.uuid4())
    db_manager.execute_insert(
        """
        INSERT INTO vacation (vacationID, userID, start, end, name, description, created, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (vacation_id, user_id, start, end, name, description, datetime.now(), user_id),
    )

    flash(f'Vacation "{name}" added.', 'success')
    return _redirect_to_index(username)


@vacation_bp.route('/delete/post/<vacation_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_HABIT)
@permission_required_write(PERM_HABIT)
def delete(username: str, vacation_id: str):
    """
    Delete a vacation period.

    Path Parameters
    ---------------
    vacation_id : str   The vacationID UUID to delete.
    """
    user_id = session['user_id']

    row = db_manager.execute_one(
        'SELECT name FROM vacation WHERE vacationID = %s AND userID = %s',
        (vacation_id, user_id),
    )

    if row is None:
        flash('Vacation not found.', 'error')
        return _redirect_to_index(username)

    db_manager.execute_update(
        'DELETE FROM vacation WHERE vacationID = %s AND userID = %s',
        (vacation_id, user_id),
    )

    flash(f'Vacation "{row["name"]}" deleted.', 'success')
    return _redirect_to_index(username)
