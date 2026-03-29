"""
Triage Routes
=============
Flask blueprint for Gmail and Calendar triage.

URL patterns
------------
GET  /<username>/triage/index  -> email + calendar triage view

This feature requires Google OAuth tokens with Gmail and Calendar scopes.
If tokens are absent or expired, the user is prompted to re-authenticate.

Triage table records processed Gmail message IDs so that already-triaged
messages are not shown again.

Dependencies
------------
    app.services.google_services  – Gmail and Calendar API wrappers
"""

from datetime import datetime

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
    PERM_TRIAGE,
    login_required,
    permission_required_read,
    permission_required_write,
)

triage_bp = Blueprint('triage', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_user_tokens(user_id: str) -> dict | None:
    """Return Google OAuth tokens for a user."""
    return db_manager.execute_one(
        'SELECT access_token, refresh_token, token_expires FROM user WHERE userID = %s',
        (user_id,),
    )


def _get_triaged_ids(user_id: str) -> set:
    """Return the set of gmailIDs already triaged by this user."""
    rows = db_manager.execute_query(
        'SELECT gmailID FROM triage WHERE userID = %s AND gmailID IS NOT NULL',
        (user_id,),
    )
    return {row['gmailID'] for row in rows}


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@triage_bp.route('/index')
@login_required
@permission_required_read(PERM_TRIAGE)
def index(username: str):
    """
    Email and calendar triage view.

    Fetches unread emails and upcoming calendar events via Google APIs,
    filtering out already-triaged messages.  Falls back gracefully when
    Google tokens are unavailable.
    """
    user_id = session['user_id']

    emails = []
    calendar_events = []
    google_error = None

    try:
        from app.services.google_services import get_gmail_messages, get_calendar_events  # noqa: PLC0415
        tokens = _get_user_tokens(user_id)

        if tokens and tokens.get('access_token'):
            triaged_ids = _get_triaged_ids(user_id)
            all_emails = get_gmail_messages(tokens['access_token'], tokens.get('refresh_token'))
            emails = [e for e in all_emails if e.get('id') not in triaged_ids]
            calendar_events = get_calendar_events(tokens['access_token'], tokens.get('refresh_token'))
        else:
            google_error = 'Google account not connected. Re-authenticate to enable triage.'

    except ImportError:
        google_error = 'Google services module not available.'
    except Exception as exc:  # noqa: BLE001
        google_error = f'Error fetching data from Google: {exc}'

    return render_template(
        'triage_index.html',
        emails=emails,
        calendar_events=calendar_events,
        google_error=google_error,
        username=username,
    )
