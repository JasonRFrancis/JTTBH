"""
Appointment Routes
==================
Flask blueprint for Calendly-style appointment scheduling.

URL patterns
------------
GET  /<username>/appointment/index     -> manage appointment types (authenticated)
GET  /book/<url>                       -> public booking page (no auth required)

The appointment feature allows users to define appointment types (name, duration,
URL slug) and expose a public booking page where external visitors can select
available time slots.

Schema tables used:
    appointment        – appointment type definitions
    appointment_block  – available time blocks
    appointment_invite – booked invitations

Note: The /book/<url> route must be registered at the application level (not under
the /<username>/ prefix) to be publicly accessible without a username in the URL.
Since this blueprint is mounted at /<username>/appointment, the public booking page
is handled as a special case within this blueprint using a separate URL prefix in
the app factory, or could be moved to a separate blueprint.
"""

import uuid
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
    PERM_APPOINTMENT,
    login_required,
    permission_required_read,
    permission_required_write,
)

appointment_bp = Blueprint('appointment', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_appointments(user_id: str) -> list[dict]:
    """Return all appointment types for a user."""
    return db_manager.execute_query(
        """
        SELECT appointmentID, name, description, url, active, location, type, color
        FROM appointment
        WHERE userID = %s
        ORDER BY id
        """,
        (user_id,),
    )


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@appointment_bp.route('/index')
@login_required
@permission_required_read(PERM_APPOINTMENT)
def index(username: str):
    """
    Manage appointment types for the authenticated user.

    Template context
    ----------------
    appointments : list[dict]   All appointment type records.
    username     : str
    """
    user_id = session['user_id']
    appointments = _get_appointments(user_id)

    return render_template(
        'appointment_index.html',
        appointments=appointments,
        username=username,
    )
