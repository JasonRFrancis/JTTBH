"""
Journal Routes
==============
Flask blueprint for daily journal questions, answers, and mood tracking.

URL patterns
------------
GET  /<username>/journal/index
GET  /<username>/journal/index/<date_str>
GET  /<username>/journal/questions
GET  /<username>/journal/mood/settings

POST /<username>/journal/answer/post/<question_id>
POST /<username>/journal/mood/post
POST /<username>/journal/question/create/post
POST /<username>/journal/mood/category/create/post
POST /<username>/journal/mood/value/create/post

Question selection by day of year
----------------------------------
Questions are stored with a ``day`` column (1-366).  On each journal load the
current day-of-year is computed and all questions for that day are fetched.

Mood tracking
-------------
Mood categories are user-defined groups (e.g. "Energy", "Anxiety").
Mood values are the selectable options per category (e.g. "High", "Low").
Each journal entry records one value per category per day.
"""

import uuid
from datetime import date, datetime

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
    PERM_JOURNAL,
    login_required,
    permission_required_read,
    permission_required_write,
)

journal_bp = Blueprint('journal', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(date_str: str) -> date | None:
    """Parse YYYY-MM-DD string; return None on failure."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _redirect_to_index(username: str, entry_date: date | None = None):
    """Redirect to the journal index, optionally for a specific date."""
    if entry_date:
        return redirect(url_for(
            'journal.index_date', username=username, date_str=entry_date.isoformat()
        ))
    return redirect(url_for('journal.index', username=username))


def _get_questions_for_day(day_of_year: int) -> list[dict]:
    """Fetch all questions assigned to a specific day of the year."""
    return db_manager.execute_query(
        'SELECT questionID, question, day FROM journal_question WHERE day = %s ORDER BY id',
        (day_of_year,),
    )


def _get_answers_for_date(user_id: str, entry_date: date) -> dict:
    """Return answers keyed by questionID for a given user and date."""
    rows = db_manager.execute_query(
        """
        SELECT ja.questionID, ja.answerID, ja.answer
        FROM journal_answer ja
        WHERE ja.userID = %s
          AND ja.answered = %s
          AND ja.id = (
              SELECT MAX(ja2.id) FROM journal_answer ja2
              WHERE ja2.userID = ja.userID
                AND ja2.questionID = ja.questionID
                AND ja2.answered = ja.answered
          )
        """,
        (user_id, entry_date),
    )
    return {row['questionID']: row for row in rows}


def _get_categories(user_id: str) -> list[dict]:
    """Fetch mood categories for a user."""
    return db_manager.execute_query(
        'SELECT categoryID, name FROM journal_moodCategory WHERE userID = %s ORDER BY id',
        (user_id,),
    )


def _get_mood_values_for_category(user_id: str, category_id: str | None) -> list[dict]:
    """Fetch mood value options for a specific category (or global defaults if None)."""
    if category_id is None:
        return db_manager.execute_query(
            """
            SELECT categoryID, value, name, color, icon
            FROM journal_moodValue
            WHERE userID = %s AND categoryID IS NULL
            ORDER BY value
            """,
            (user_id,),
        )
    return db_manager.execute_query(
        """
        SELECT categoryID, value, name, color, icon
        FROM journal_moodValue
        WHERE userID = %s AND categoryID = %s
        ORDER BY value
        """,
        (user_id, category_id),
    )


def _get_current_moods(user_id: str, entry_date: date) -> dict:
    """Return dict of categoryID -> value for the most recent mood entry per category."""
    rows = db_manager.execute_query(
        """
        SELECT jm.categoryID, jm.value
        FROM journal_mood jm
        WHERE jm.userID = %s
          AND jm.answered = %s
          AND jm.id = (
              SELECT MAX(jm2.id) FROM journal_mood jm2
              WHERE jm2.userID = jm.userID
                AND jm2.categoryID = jm.categoryID
                AND jm2.answered = jm.answered
          )
        """,
        (user_id, entry_date),
    )
    return {row['categoryID']: row['value'] for row in rows}


def _build_context(user_id: str, username: str, entry_date: date) -> dict:
    """Build the full template context for a journal day view."""
    day_of_year = entry_date.timetuple().tm_yday
    questions = _get_questions_for_day(day_of_year)
    answers = _get_answers_for_date(user_id, entry_date)
    categories = _get_categories(user_id)
    current_moods = _get_current_moods(user_id, entry_date)

    # Build a per-category dict of value options.
    mood_values_by_category: dict[str, list] = {}
    for cat in categories:
        mood_values_by_category[cat['categoryID']] = _get_mood_values_for_category(
            user_id, cat['categoryID']
        )

    return {
        'username': username,
        'entry_date': entry_date.isoformat(),
        'entry_date_obj': entry_date,
        'today': user_today().isoformat(),
        'questions': questions,
        'answers': answers,
        'categories': categories,
        'current_moods': current_moods,
        'mood_values_by_category': mood_values_by_category,
    }


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@journal_bp.route('/index')
@login_required
@permission_required_read(PERM_JOURNAL)
def index(username: str):
    """Redirect to today's dated journal URL."""
    return redirect(url_for(
        'journal.index_date', username=username, date_str=user_today().isoformat()
    ))


@journal_bp.route('/index/<date_str>')
@login_required
@permission_required_read(PERM_JOURNAL)
def index_date(username: str, date_str: str):
    """
    Display the journal for a specific date.

    Shows daily questions with existing answers, and the mood tracker.
    """
    entry_date = _parse_date(date_str) or user_today()
    user_id = session['user_id']
    context = _build_context(user_id, username, entry_date)
    return render_template('journal_index.html', **context)


@journal_bp.route('/questions')
@login_required
@permission_required_read(PERM_JOURNAL)
def questions(username: str):
    """
    Manage journal questions (admin-style view).

    Lists all questions grouped by day of year.
    """
    all_questions = db_manager.execute_query(
        'SELECT questionID, question, day FROM journal_question ORDER BY day, id',
    )
    return render_template(
        'journal_questions.html',
        all_questions=all_questions,
        username=username,
    )


@journal_bp.route('/mood/settings')
@login_required
@permission_required_read(PERM_JOURNAL)
def mood_settings(username: str):
    """
    Manage mood categories and value options.
    """
    user_id = session['user_id']
    categories = _get_categories(user_id)
    all_values = db_manager.execute_query(
        'SELECT categoryID, value, name, color, icon FROM journal_moodValue WHERE userID = %s ORDER BY categoryID, value',
        (user_id,),
    )
    return render_template(
        'journal_mood_settings.html',
        categories=categories,
        all_values=all_values,
        username=username,
    )


# ---------------------------------------------------------------------------
# POST routes (PRG pattern)
# ---------------------------------------------------------------------------

@journal_bp.route('/answer/post/<question_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_JOURNAL)
@permission_required_write(PERM_JOURNAL)
def save_answer(username: str, question_id: str):
    """
    Save (or update) an answer to a daily question.

    Inserts a new row each time, which provides full history.
    The most recent row per (userID, questionID, answered) is the current state.

    Form fields
    -----------
    answer   : str   Required.
    answered : str   ISO date string (YYYY-MM-DD); defaults to today.
    """
    user_id = session['user_id']
    answer_text = request.form.get('answer', '').strip()
    answered_str = request.form.get('answered', '').strip()
    answered = _parse_date(answered_str) or user_today()

    if not answer_text:
        flash('Answer cannot be empty.', 'error')
        return _redirect_to_index(username, answered)

    answer_id = str(uuid.uuid4())
    db_manager.execute_insert(
        """
        INSERT INTO journal_answer (answerID, userID, questionID, answer, answered, created, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (answer_id, user_id, question_id, answer_text, answered, datetime.now(), user_id),
    )

    flash('Answer saved.', 'success')
    return _redirect_to_index(username, answered)


@journal_bp.route('/mood/post', methods=['POST'])
@login_required
@permission_required_read(PERM_JOURNAL)
@permission_required_write(PERM_JOURNAL)
def save_mood(username: str):
    """
    Record mood entries for one or more categories.

    Expects form fields named ``mood_<categoryID>`` with an integer value.
    A special field name ``mood_default`` is used when no custom categories exist.

    Form fields
    -----------
    answered         : str   ISO date string; defaults to today.
    mood_<categoryID>: int   Value to record for the given category.
    """
    user_id = session['user_id']
    answered_str = request.form.get('answered', '').strip()
    answered = _parse_date(answered_str) or user_today()

    saved_count = 0
    for key, value in request.form.items():
        if not key.startswith('mood_'):
            continue
        category_id = key[5:]  # strip 'mood_' prefix
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            continue

        mood_id = str(uuid.uuid4())
        db_manager.execute_insert(
            """
            INSERT INTO journal_mood (moodID, userID, categoryID, value, answered, created, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (mood_id, user_id, category_id, int_value, answered, datetime.now(), user_id),
        )
        saved_count += 1

    if saved_count:
        flash('Mood recorded.', 'success')
    else:
        flash('No mood values submitted.', 'error')

    return _redirect_to_index(username, answered)


@journal_bp.route('/question/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_JOURNAL)
@permission_required_write(PERM_JOURNAL)
def question_create(username: str):
    """
    Add a new daily question.

    Form fields
    -----------
    question : str   Required.
    day      : int   Day of year (1-366). Required.
    """
    user_id = session['user_id']
    question_text = request.form.get('question', '').strip()
    day_str = request.form.get('day', '').strip()

    if not question_text:
        flash('Question text is required.', 'error')
        return redirect(url_for('journal.questions', username=username))

    try:
        day = int(day_str)
        if not 1 <= day <= 366:
            raise ValueError
    except (ValueError, TypeError):
        flash('Day must be a number between 1 and 366.', 'error')
        return redirect(url_for('journal.questions', username=username))

    question_id = str(uuid.uuid4())
    db_manager.execute_insert(
        """
        INSERT INTO journal_question (questionID, question, day, created, created_by)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (question_id, question_text, day, datetime.now(), user_id),
    )

    flash('Question added.', 'success')
    return redirect(url_for('journal.questions', username=username))


@journal_bp.route('/mood/category/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_JOURNAL)
@permission_required_write(PERM_JOURNAL)
def mood_category_create(username: str):
    """
    Add a new mood category (e.g. "Energy", "Anxiety").

    Form fields
    -----------
    name : str   Required.
    """
    user_id = session['user_id']
    name = request.form.get('name', '').strip()

    if not name:
        flash('Category name is required.', 'error')
        return redirect(url_for('journal.mood_settings', username=username))

    category_id = str(uuid.uuid4())
    db_manager.execute_insert(
        """
        INSERT INTO journal_moodCategory (categoryID, userID, name, created, created_by)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (category_id, user_id, name, datetime.now(), user_id),
    )

    flash('Mood category added.', 'success')
    return redirect(url_for('journal.mood_settings', username=username))


@journal_bp.route('/mood/value/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_JOURNAL)
@permission_required_write(PERM_JOURNAL)
def mood_value_create(username: str):
    """
    Add a new mood value option for a category.

    Form fields
    -----------
    category_id : str   Category UUID; leave blank for global defaults.
    value       : int   Required. Numeric value (used for ordering/comparison).
    name        : str   Required. Display label.
    color       : str   Optional. CSS color string.
    icon        : str   Optional. Icon identifier or emoji.
    """
    user_id = session['user_id']
    category_id = request.form.get('category_id', '').strip() or None
    value_str = request.form.get('value', '').strip()
    name = request.form.get('name', '').strip()
    color = request.form.get('color', '').strip() or '#cccccc'
    icon = request.form.get('icon', '').strip() or None

    if not name:
        flash('Value name is required.', 'error')
        return redirect(url_for('journal.mood_settings', username=username))

    try:
        value = int(value_str)
    except (ValueError, TypeError):
        flash('Value must be an integer.', 'error')
        return redirect(url_for('journal.mood_settings', username=username))

    db_manager.execute_insert(
        """
        INSERT INTO journal_moodValue (categoryID, userID, value, name, color, icon, created, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (category_id, user_id, value, name, color, icon, datetime.now(), user_id),
    )

    flash('Mood value added.', 'success')
    return redirect(url_for('journal.mood_settings', username=username))
