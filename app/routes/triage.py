"""
Triage Routes
=============
Flask blueprint for Gmail and Calendar triage.

URL patterns
------------
GET  /<username>/triage/index                     -> inbox + calendar triage view
POST /<username>/triage/todo/post/<gmail_id>       -> email -> daily todo
POST /<username>/triage/project/post/<gmail_id>    -> email -> new project

Requires Google OAuth tokens with the gmail.readonly + calendar.readonly scopes
(minted at login; if the stored token has no usable refresh token the view shows
a "Reconnect Google" link -> auth.google_login, which forces the consent screen).

The ``triage`` table records handled Gmail message IDs so converted messages drop
off the list on the next load. Unhandled mail is simply left alone.

Dependencies
------------
    app.services.google_services.google_services  -- Gmail / Calendar API wrapper
"""

import uuid

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
from app.services.timezone_utils import user_today
from app.services.decorators import (
    PERM_TRIAGE,
    login_required,
    permission_required_read,
    permission_required_write,
)
from app.models.todo_model import TodoModel
from app.models.project_model import ProjectModel

triage_bp = Blueprint('triage', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_triaged_ids(user_id: str) -> set:
    """gmailIDs this user has already converted (todo/project)."""
    rows = db_manager.execute_query(
        'SELECT gmailID FROM triage WHERE userID = %s AND gmailID IS NOT NULL',
        (user_id,),
    )
    return {row['gmailID'] for row in rows}


def _mark_triaged(user_id: str, gmail_id: str) -> None:
    """Record that *gmail_id* has been handled (idempotent)."""
    if gmail_id in _get_triaged_ids(user_id):
        return
    db_manager.execute_insert(
        """
        INSERT INTO triage (triageID, userID, gmailID, completed, created, created_by)
        VALUES (%s, %s, %s, NOW(), NOW(), %s)
        """,
        (str(uuid.uuid4()), user_id, gmail_id, user_id),
    )


def _redirect_index(username: str):
    return redirect(url_for('triage.index', username=username))


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------

@triage_bp.route('/index')
@login_required
@permission_required_read(PERM_TRIAGE)
def index(username: str):
    """Inbox + calendar triage view."""
    user_id = session['user_id']

    emails = []
    calendar_events = []
    google_error = None

    try:
        from app.services.google_services import google_services  # noqa: PLC0415

        creds = google_services.get_credentials(user_id)
        if not (creds and creds.valid):
            google_error = 'Google account not connected. Reconnect to enable triage.'
        else:
            triaged = _get_triaged_ids(user_id)
            emails = [
                e for e in google_services.get_gmail_messages(user_id)
                if e.get('id') not in triaged
            ]
            calendar_events = google_services.get_calendar_events(user_id)
    except Exception as exc:  # noqa: BLE001
        google_error = f'Error fetching data from Google: {exc}'

    return render_template(
        'triage_index.html',
        emails=emails,
        calendar_events=calendar_events,
        google_error=google_error,
        username=username,
    )


# ---------------------------------------------------------------------------
# POST (PRG)
# ---------------------------------------------------------------------------

@triage_bp.route('/todo/post/<gmail_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TRIAGE)
@permission_required_write(PERM_TRIAGE)
def to_todo(username: str, gmail_id: str):
    """Create today's daily todo from an email, then drop it from triage."""
    user_id = session['user_id']
    subject = (request.form.get('subject', '') or '').strip()[:255] or '(no subject)'

    TodoModel.create(
        user_id=user_id,
        title=subject,
        due=user_today(),
        list_type='daily',
    )
    _mark_triaged(user_id, gmail_id)

    flash(f'Added to today’s todo list: "{subject}"', 'success')
    return _redirect_index(username)


@triage_bp.route('/project/post/<gmail_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TRIAGE)
@permission_required_write(PERM_TRIAGE)
def to_project(username: str, gmail_id: str):
    """Create a new project from an email, then drop it from triage."""
    user_id = session['user_id']
    subject = (request.form.get('subject', '') or '').strip()[:255] or '(no subject)'
    snippet = (request.form.get('snippet', '') or '').strip() or None

    project_id = ProjectModel.create(user_id, name=subject, description=snippet)
    _mark_triaged(user_id, gmail_id)

    flash(f'Created project: "{subject}"', 'success')
    return redirect(url_for('project.view', username=username, project_id=project_id))
