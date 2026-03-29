"""
JTTBH Habit Routes
==================
Habit tracker feature: calendar view, heatmap, and settings.

URL Patterns
------------
GET  /<username>/habit/index                           – Main calendar view (28-day window)
GET  /<username>/habit/index/<date_str>                – Calendar for a specific reference date
GET  /<username>/habit/heatmap                         – GitHub-style heatmap view
GET  /<username>/habit/settings                        – Manage habits (add / edit / delete)
GET  /<username>/habit/settings/<habit_id>             – Edit a specific habit (renders settings)

POST /<username>/habit/toggle/post/<habit_id>/<date_str>  – Toggle completion for a date
POST /<username>/habit/create/post                        – Create a new habit
POST /<username>/habit/update/post/<habit_id>             – Update habit properties
POST /<username>/habit/delete/post/<habit_id>             – Soft-delete a habit
POST /<username>/habit/reorder/post                       – Batch-update grid positions

Permissions
-----------
All routes require ``PERM_HABIT`` read access.
POST routes additionally require ``PERM_HABIT`` write access.

PRG pattern
-----------
All POST routes redirect to a GET endpoint on success (or failure for forms)
and communicate outcome via a flash message.  AJAX toggle requests return JSON
instead of a redirect.
"""

import json
from datetime import date, timedelta

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    jsonify,
    abort,
)

from app.models.habit_model import HabitModel, dayweek_label
from app.services.decorators import (
    login_required,
    permission_required_read,
    permission_required_write,
    PERM_HABIT,
)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

habit_bp = Blueprint('habit', __name__)


# ---------------------------------------------------------------------------
# Template filter
# ---------------------------------------------------------------------------

@habit_bp.app_template_filter('dayweek_label')
def dayweek_label_filter(dayweek):
    """Jinja2 filter: convert dayweek bitmask to readable day labels."""
    return dayweek_label(dayweek)


@habit_bp.app_template_filter('format_day_short')
def format_day_short_filter(d):
    """Jinja2 filter: format a date as 'Mon Mar 25'."""
    if isinstance(d, str):
        try:
            d = date.fromisoformat(d)
        except ValueError:
            return str(d)
    return d.strftime('%a %b %-d')


# ---------------------------------------------------------------------------
# Helper: parse date from URL string
# ---------------------------------------------------------------------------

def _parse_date(date_str: str | None, default: date = None) -> date:
    """Parse a YYYY-MM-DD string; return default (or today) on failure."""
    if default is None:
        default = date.today()
    if not date_str:
        return default
    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# Helper: compute today's completion stats
# ---------------------------------------------------------------------------

def _today_stats(user_id: str) -> tuple[int, int]:
    """
    Return (completed_count, total_count) for today's applicable habits.
    """
    today   = date.today()
    grid    = HabitModel.get_grid_for_date(user_id, today)
    total     = sum(1 for cell in grid if cell['habitID'] and cell['applies'])
    completed = sum(1 for cell in grid if cell['habitID'] and cell['applies'] and cell['completed'] == 1)
    return completed, total


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@habit_bp.route('/index', defaults={'date_str': None})
@habit_bp.route('/index/<date_str>')
@login_required
@permission_required_read(PERM_HABIT)
def index(username: str, date_str: str):
    """Render the main calendar view (28-day window)."""
    user_id  = session['user_id']
    ref_date = _parse_date(date_str)

    calendar_data    = HabitModel.get_calendar_data(user_id, ref_date)
    streaks          = HabitModel.calculate_streaks(user_id)
    today_completed, today_total = _today_stats(user_id)

    # Attach streak to each calendar day's grid cells
    for day in calendar_data:
        for cell in day['grid']:
            if cell['habitID']:
                cell['streak'] = streaks.get(cell['habitID'], 0)

    return render_template(
        'habit_index.html',
        username=username,
        area='habit',
        ref_date=ref_date,
        calendar_data=calendar_data,
        today_completed=today_completed,
        today_total=today_total,
        streaks=streaks,
    )


@habit_bp.route('/heatmap')
@login_required
@permission_required_read(PERM_HABIT)
def heatmap(username: str):
    """Render the GitHub-style heatmap view."""
    user_id = session['user_id']

    heatmap_data = HabitModel.get_heatmap_data(user_id, days=365)
    streaks      = HabitModel.calculate_streaks(user_id)
    habits       = HabitModel.get_habits(user_id)

    # Attach streak to each habit dict for template
    habits_with_streaks = []
    for habit in habits:
        habit = dict(habit)
        habit['streak'] = streaks.get(habit['habitID'], 0)
        habits_with_streaks.append(habit)

    # Group heatmap data into weeks (7 days per week, Sunday-first)
    # Pad the beginning of the first week so day 0 = Sunday
    if heatmap_data:
        first_day = heatmap_data[0]['date']
        # Python weekday(): Mon=0...Sun=6  -> Sun-first offset = (weekday+1)%7
        pad_days = (first_day.weekday() + 1) % 7
    else:
        pad_days = 0

    padded = [None] * pad_days + heatmap_data
    heatmap_weeks = []
    for i in range(0, len(padded), 7):
        week = padded[i:i + 7]
        # Pad end of last week with None
        while len(week) < 7:
            week.append(None)
        heatmap_weeks.append(week)

    return render_template(
        'habit_heatmap.html',
        username=username,
        area='habit',
        heatmap_weeks=heatmap_weeks,
        heatmap_data=heatmap_data,
        habits_with_streaks=habits_with_streaks,
    )


@habit_bp.route('/settings', defaults={'habit_id': None})
@habit_bp.route('/settings/<habit_id>')
@login_required
@permission_required_read(PERM_HABIT)
def settings(username: str, habit_id: str):
    """Render the habit settings / management page."""
    user_id = session['user_id']
    habits  = HabitModel.get_habits(user_id)
    icons   = HabitModel.get_icons()

    # If a specific habit_id was given, scroll/highlight that habit
    edit_habit = None
    if habit_id:
        edit_habit = HabitModel.get_habit_by_id(habit_id, user_id)

    return render_template(
        'habit_settings.html',
        username=username,
        area='habit',
        habits=habits,
        icons=icons,
        edit_habit=edit_habit,
    )


# ---------------------------------------------------------------------------
# POST routes
# ---------------------------------------------------------------------------

@habit_bp.route('/toggle/post/<habit_id>/<date_str>', methods=['POST'])
@login_required
@permission_required_write(PERM_HABIT)
def toggle(username: str, habit_id: str, date_str: str):
    """
    Toggle completion status for a habit on a given date.

    If the request has the X-Requested-With: XMLHttpRequest header,
    returns JSON {'completed': 1 | null}.
    Otherwise redirects to the calendar index page (PRG pattern).
    """
    user_id    = session['user_id']
    entry_date = _parse_date(date_str)

    result = HabitModel.toggle_entry(habit_id, user_id, entry_date)

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return jsonify({'completed': result['completed']})

    # PRG fallback
    flash('Habit updated.', 'success')
    return redirect(url_for('habit.index', username=username, date_str=date_str))


@habit_bp.route('/create/post', methods=['POST'])
@login_required
@permission_required_write(PERM_HABIT)
def create(username: str):
    """Create a new habit from the settings form."""
    user_id = session['user_id']
    name    = request.form.get('name', '').strip()

    if not name:
        flash('Habit name is required.', 'error')
        return redirect(url_for('habit.settings', username=username))

    # Parse dayweek bitmask from checkboxes (each submits its bit value)
    dayweek_values = request.form.getlist('dayweek')
    dayweek = 0
    for v in dayweek_values:
        try:
            dayweek |= int(v)
        except (ValueError, TypeError):
            pass
    if dayweek == 0:
        dayweek = 127  # default: all days

    # Parse position
    try:
        position = int(request.form.get('position', 0))
        position = max(0, min(24, position))
    except (ValueError, TypeError):
        position = 0

    description   = request.form.get('description', '').strip() or None
    action        = request.form.get('action', '').strip() or None
    color         = request.form.get('color', '').strip() or None
    icon          = request.form.get('icon', '').strip() or None
    vacation_mode = 1 if request.form.get('vacation_mode') else 0
    active        = 1

    HabitModel.create(
        user_id=user_id,
        name=name,
        description=description,
        action=action,
        color=color,
        icon=icon,
        active=active,
        dayweek=dayweek,
        position=position,
        vacation_mode=vacation_mode,
    )

    flash(f'Habit "{name}" created.', 'success')
    return redirect(url_for('habit.settings', username=username))


@habit_bp.route('/update/post/<habit_id>', methods=['POST'])
@login_required
@permission_required_write(PERM_HABIT)
def update(username: str, habit_id: str):
    """Update an existing habit from the settings edit form."""
    user_id = session['user_id']
    name    = request.form.get('name', '').strip()

    if not name:
        flash('Habit name is required.', 'error')
        return redirect(url_for('habit.settings', username=username, habit_id=habit_id))

    # Parse dayweek bitmask
    dayweek_values = request.form.getlist('dayweek')
    dayweek = 0
    for v in dayweek_values:
        try:
            dayweek |= int(v)
        except (ValueError, TypeError):
            pass
    if dayweek == 0:
        dayweek = 127

    try:
        position = int(request.form.get('position', 0))
        position = max(0, min(24, position))
    except (ValueError, TypeError):
        position = 0

    description   = request.form.get('description', '').strip() or None
    action        = request.form.get('action', '').strip() or None
    color         = request.form.get('color', '').strip() or None
    icon          = request.form.get('icon', '').strip() or None
    vacation_mode = 1 if request.form.get('vacation_mode') else 0
    active        = 1 if request.form.get('active') else 0

    HabitModel.update(
        habit_id=habit_id,
        user_id=user_id,
        name=name,
        description=description,
        action=action,
        color=color,
        icon=icon,
        active=active,
        dayweek=dayweek,
        position=position,
        vacation_mode=vacation_mode,
    )

    flash(f'Habit "{name}" updated.', 'success')
    return redirect(url_for('habit.settings', username=username))


@habit_bp.route('/delete/post/<habit_id>', methods=['POST'])
@login_required
@permission_required_write(PERM_HABIT)
def delete(username: str, habit_id: str):
    """Soft-delete a habit (inserts a record with name=NULL)."""
    user_id = session['user_id']

    habit = HabitModel.get_habit_by_id(habit_id, user_id)
    if habit is None:
        flash('Habit not found.', 'error')
        return redirect(url_for('habit.settings', username=username))

    habit_name = habit['name']
    HabitModel.delete(habit_id, user_id)

    flash(f'Habit "{habit_name}" deleted.', 'success')
    return redirect(url_for('habit.settings', username=username))


@habit_bp.route('/reorder/post', methods=['POST'])
@login_required
@permission_required_write(PERM_HABIT)
def reorder(username: str):
    """
    Batch-update grid positions for multiple habits.

    Expects JSON body: [{"habitID": "...", "position": 0}, ...]
    Or form data: positions=<JSON array>.
    """
    user_id = session['user_id']

    # Accept JSON or form-encoded
    if request.is_json:
        items = request.get_json(silent=True) or []
    else:
        raw = request.form.get('positions', '[]')
        try:
            items = json.loads(raw)
        except (ValueError, TypeError):
            items = []

    if not isinstance(items, list):
        abort(400)

    for item in items:
        if not isinstance(item, dict):
            continue
        h_id = item.get('habitID')
        pos  = item.get('position')
        if h_id and pos is not None:
            try:
                pos = max(0, min(24, int(pos)))
            except (ValueError, TypeError):
                continue
            HabitModel.update(habit_id=h_id, user_id=user_id, position=pos)

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return jsonify({'status': 'ok'})

    flash('Habit positions saved.', 'success')
    return redirect(url_for('habit.settings', username=username))
