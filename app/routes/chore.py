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

from datetime import date

from flask import (
    Blueprint,
    render_template,
    session,
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
    today = date.today()
    day_of_week_bit = _DAY_BITMASK[today.weekday()]

    household = _get_user_household(user_id)
    todays_chores = []
    all_chores = []

    if household:
        todays_chores = _get_todays_chores(household['householdID'], day_of_week_bit)
        all_chores = _get_all_chores(household['householdID'])

    return render_template(
        'chore_index.html',
        household=household,
        todays_chores=todays_chores,
        all_chores=all_chores,
        today=today,
        day_name=today.strftime('%A'),
        username=username,
    )
