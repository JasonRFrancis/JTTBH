from datetime import date, datetime
from zoneinfo import ZoneInfo


def today_for_tz(tz_name: str) -> date:
    """Return the current date in the given IANA timezone name."""
    try:
        return datetime.now(ZoneInfo(tz_name or 'UTC')).date()
    except (KeyError, Exception):
        return date.today()


def user_today() -> date:
    """Return today's date in the current user's timezone (reads Flask session)."""
    from flask import session
    return today_for_tz(session.get('timezone', 'UTC'))
