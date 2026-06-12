"""
Chore Routes
============
Flask blueprint for household chore tracking.

URL patterns
------------
GET  /<username>/chore/index  -> today's chores view

Chores are linked to households via the chore_list and chore_listItem tables.
The chore_listItemDay and chore_listItemMonth tables encode scheduling using
bitmask columns:

    day_of_week : bit 1=Sunday, 2=Monday, 4=Tuesday, 8=Wednesday,
                      16=Thursday, 32=Friday, 64=Saturday
    season      : bit 1=spring, 2=summer, 4=fall, 8=winter
    month       : bit 1=Jan, 2=Feb, 4=Mar, ..., 2048=Dec

Today's chores are those whose day_of_week bitmask includes today's day.

Schema note: The chore table does not have a userID column -- chores are
shared across households.  User membership is tracked via household_member.
This means the household lookup is required before querying chores.
"""

import secrets
import uuid
from datetime import date

from app.services.timezone_utils import user_today

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
    PERM_CHORE,
    login_required,
    permission_required_read,
)

chore_bp = Blueprint('chore', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_user_household(user_id: str) -> dict | None:
    """Return the household for the given user (first one found)."""
    return db_manager.execute_one(
        """
        SELECT h.householdID, h.name
        FROM household h
        JOIN household_member hm ON hm.householdID = h.householdID
        WHERE hm.userID = %s
        ORDER BY hm.id
        LIMIT 1
        """,
        (user_id,),
    )


def _get_todays_chores(household_id: str, day_of_week_bit: int) -> list[dict]:
    """
    Return chores scheduled for today's day of week.

    day_of_week_bit must be the bitmask value for today:
        Sunday=1, Monday=2, Tuesday=4, Wednesday=8,
        Thursday=16, Friday=32, Saturday=64
    """
    return db_manager.execute_query(
        """
        SELECT c.choreID, c.name, c.description,
               cl.name AS list_name, cl.choreListID
        FROM chore_listItemDay clid
        JOIN chore_list cl ON cl.choreListID = clid.choreListID
        JOIN chore c ON c.choreID = clid.choreID
        WHERE cl.householdID = %s
          AND (clid.day_of_week & %s) != 0
        ORDER BY cl.name, c.name
        """,
        (household_id, day_of_week_bit),
    )


def _get_all_chores(household_id: str) -> list[dict]:
    """Return all chores associated with a household."""
    return db_manager.execute_query(
        """
        SELECT c.choreID, c.name, c.description,
               cl.name AS list_name, cl.choreListID
        FROM chore_list cl
        JOIN chore_listItemDay clid ON clid.choreListID = cl.choreListID
        JOIN chore c ON c.choreID = clid.choreID
        WHERE cl.householdID = %s
        ORDER BY cl.name, c.name
        """,
        (household_id,),
    )


def _get_invite_token(household_id: str, user_id: str) -> str:
    """Get or create a stable invite token for the household, stored in user_preference."""
    pref_key = f'hh_invite_{household_id}'
    row = db_manager.execute_one(
        "SELECT value FROM user_preference WHERE preference = %s ORDER BY id DESC LIMIT 1",
        (pref_key,),
    )
    if row:
        return row['value']
    token = secrets.token_urlsafe(24)
    db_manager.execute_insert(
        "INSERT INTO user_preference (userID, preference, value, created, created_by) VALUES (%s, %s, %s, NOW(), %s)",
        (user_id, pref_key, token, user_id),
    )
    return token


# Day bitmask mapping: Python weekday() Monday=0, but chore schema Sunday=1.
_DAY_BITMASK = {
    6: 1,   # Sunday
    0: 2,   # Monday
    1: 4,   # Tuesday
    2: 8,   # Wednesday
    3: 16,  # Thursday
    4: 32,  # Friday
    5: 64,  # Saturday
}


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@chore_bp.route('/index')
@login_required
@permission_required_read(PERM_CHORE)
def index(username: str):
    """
    Display today's household chores.

    Template context
    ----------------
    household      : dict | None   User's household record.
    todays_chores  : list[dict]    Chores scheduled for today.
    all_chores     : list[dict]    All chores for the household.
    today          : date
    day_name       : str           e.g. 'Monday'
    username       : str
    """
    user_id = session['user_id']
    today = user_today()
    day_of_week_bit = _DAY_BITMASK[today.weekday()]

    household = _get_user_household(user_id)
    todays_chores = []
    all_chores = []

    if not household:
        # Auto-create a household for this user
        household_id = str(uuid.uuid4())
        db_manager.execute_insert(
            "INSERT INTO household (householdID, name, created, created_by) VALUES (%s, %s, NOW(), %s)",
            (household_id, f"{username}'s Household", user_id),
        )
        db_manager.execute_insert(
            "INSERT INTO household_member (householdID, userID, created, created_by) VALUES (%s, %s, NOW(), %s)",
            (household_id, user_id, user_id),
        )
        household = _get_user_household(user_id)
        flash('A household was created for you.', 'success')

    if household:
        todays_chores = _get_todays_chores(household['householdID'], day_of_week_bit)
        all_chores = _get_all_chores(household['householdID'])

    invite_token = _get_invite_token(household['householdID'], user_id) if household else None

    return render_template(
        'chore_index.html',
        household=household,
        todays_chores=todays_chores,
        all_chores=all_chores,
        today=today,
        day_name=today.strftime('%A'),
        username=username,
        invite_token=invite_token,
    )


@chore_bp.route('/join/<token>')
@login_required
def join_household(username: str, token: str):
    """Show confirmation page for joining a household via invite link."""
    user_id = session['user_id']
    row = db_manager.execute_one(
        "SELECT userID, preference FROM user_preference WHERE value = %s AND preference LIKE 'hh_invite_%' ORDER BY id DESC LIMIT 1",
        (token,),
    )
    if not row:
        flash('Invalid or expired invite link.', 'error')
        return redirect(url_for('chore.index', username=username))

    household_id = row['preference'].replace('hh_invite_', '')

    existing = db_manager.execute_one(
        "SELECT id FROM household_member WHERE householdID = %s AND userID = %s",
        (household_id, user_id),
    )
    if existing:
        flash('You are already in this household.', 'message')
        return redirect(url_for('chore.index', username=username))

    household = db_manager.execute_one(
        "SELECT name FROM household WHERE householdID = %s ORDER BY id LIMIT 1",
        (household_id,),
    )
    return render_template(
        'chore_join.html',
        username=username,
        household_id=household_id,
        household_name=household['name'] if household else 'Unknown Household',
        token=token,
    )


@chore_bp.route('/join/post', methods=['POST'])
@login_required
def join_household_post(username: str):
    """Accept a household invite."""
    user_id = session['user_id']
    household_id = request.form.get('household_id', '').strip()
    token = request.form.get('token', '').strip()

    # Verify token
    row = db_manager.execute_one(
        "SELECT id FROM user_preference WHERE value = %s AND preference = %s",
        (token, f'hh_invite_{household_id}'),
    )
    if not row:
        flash('Invalid invite link.', 'error')
        return redirect(url_for('chore.index', username=username))

    # Add user to household (ignore if already a member)
    existing = db_manager.execute_one(
        "SELECT id FROM household_member WHERE householdID = %s AND userID = %s",
        (household_id, user_id),
    )
    if not existing:
        db_manager.execute_insert(
            "INSERT INTO household_member (householdID, userID, created, created_by) VALUES (%s, %s, NOW(), %s)",
            (household_id, user_id, user_id),
        )
    flash('You joined the household!', 'success')
    return redirect(url_for('chore.index', username=username))
