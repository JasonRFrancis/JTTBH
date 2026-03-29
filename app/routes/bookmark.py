"""
Bookmark Routes
===============
Flask blueprint for bookmark management.

URL patterns
------------
GET  /<username>/bookmark/index
GET  /<username>/bookmark/read-later

POST /<username>/bookmark/create/post
POST /<username>/bookmark/read/post/<bookmark_id>

Schema notes
------------
The bookmark table is append-only (each bookmark is a unique record with a
stable bookmarkID).  There is no insert-only update pattern here since each
row represents a distinct saved URL.  The ``read`` and ``read_later`` columns
are updated directly (the only tables that allow UPDATE per the spec's note
that insert-only applies to content records; bookmarks behave as event log).

Since the schema marks ``url`` as NOT NULL (TEXT) and there is no ``deleted``
column, bookmarks are not soft-deleted via the insert-only sentinel.  Instead,
marking as read (read=1) is the primary state transition.
"""

import uuid
from collections import defaultdict
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
    PERM_BOOKMARK,
    login_required,
    permission_required_read,
    permission_required_write,
)

bookmark_bp = Blueprint('bookmark', __name__)


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

_ALL_BOOKMARKS_SQL = """
    SELECT bookmarkID, url, title, description, tags, read_later, `read`, notes, favicon,
           DATE(created) AS created_date
    FROM bookmark
    WHERE userID = %s
    ORDER BY created DESC
"""

_READ_LATER_SQL = """
    SELECT bookmarkID, url, title, description, tags, read_later, `read`, notes, favicon,
           DATE(created) AS created_date
    FROM bookmark
    WHERE userID = %s
      AND read_later = 1
      AND `read` = 0
    ORDER BY created DESC
"""

_BOOKMARK_BY_ID_SQL = """
    SELECT bookmarkID, url, title, description, tags, read_later, `read`, notes, favicon
    FROM bookmark
    WHERE bookmarkID = %s AND userID = %s
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _redirect_to_index(username: str):
    """Redirect to the bookmark index."""
    return redirect(url_for('bookmark.index', username=username))


def _get_bookmark(bookmark_id: str, user_id: str) -> dict | None:
    """Fetch a single bookmark by ID."""
    return db_manager.execute_one(_BOOKMARK_BY_ID_SQL, (bookmark_id, user_id))


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@bookmark_bp.route('/index')
@login_required
@permission_required_read(PERM_BOOKMARK)
def index(username: str):
    """
    List all bookmarks grouped by date added.

    Template context
    ----------------
    bookmarks_by_day : dict[str, list[dict]]
        Date string (YYYY-MM-DD) -> list of bookmark dicts, newest dates first.
    username         : str
    """
    user_id = session['user_id']
    all_bookmarks = db_manager.execute_query(_ALL_BOOKMARKS_SQL, (user_id,))

    bookmarks_by_day: dict[str, list] = defaultdict(list)
    for bm in all_bookmarks:
        day_key = str(bm['created_date'])
        bookmarks_by_day[day_key].append(bm)

    # Ordered newest-first.
    ordered = dict(sorted(bookmarks_by_day.items(), reverse=True))

    return render_template(
        'bookmark_index.html',
        bookmarks_by_day=ordered,
        username=username,
    )


@bookmark_bp.route('/read-later')
@login_required
@permission_required_read(PERM_BOOKMARK)
def read_later(username: str):
    """
    List all unread read-later bookmarks.

    Template context
    ----------------
    bookmarks : list[dict]
    username  : str
    """
    user_id = session['user_id']
    bookmarks = db_manager.execute_query(_READ_LATER_SQL, (user_id,))

    return render_template(
        'bookmark_read_later.html',
        bookmarks=bookmarks,
        username=username,
    )


# ---------------------------------------------------------------------------
# POST routes (PRG pattern)
# ---------------------------------------------------------------------------

@bookmark_bp.route('/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def create(username: str):
    """
    Add a new bookmark.

    Form fields
    -----------
    url        : str   Required.
    title      : str   Optional.
    description: str   Optional.
    tags       : str   Optional comma-separated list.
    read_later : str   '1' to add to read-later list; omit or '0' otherwise.
    notes      : str   Optional personal notes.
    """
    user_id = session['user_id']
    url = request.form.get('url', '').strip()

    if not url:
        flash('URL is required.', 'error')
        return _redirect_to_index(username)

    title = request.form.get('title', '').strip() or None
    description = request.form.get('description', '').strip() or None
    tags = request.form.get('tags', '').strip() or None
    notes = request.form.get('notes', '').strip() or None
    read_later = 1 if request.form.get('read_later') == '1' else 0

    bookmark_id = str(uuid.uuid4())

    db_manager.execute_insert(
        """
        INSERT INTO bookmark
            (bookmarkID, userID, url, title, description, tags, read_later, `read`, notes, favicon, created, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, NULL, %s, %s)
        """,
        (bookmark_id, user_id, url, title, description, tags,
         read_later, notes, datetime.now(), user_id),
    )

    flash('Bookmark added.', 'success')
    return _redirect_to_index(username)


@bookmark_bp.route('/read/post/<bookmark_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def mark_read(username: str, bookmark_id: str):
    """
    Mark a bookmark as read.

    This is the one place where a direct UPDATE is used rather than the
    insert-only pattern, since bookmark rows are individual events and the
    read/read_later flags are transient state rather than content history.

    Path Parameters
    ---------------
    bookmark_id : str   The bookmarkID UUID.
    """
    user_id = session['user_id']
    bookmark = _get_bookmark(bookmark_id, user_id)

    if bookmark is None:
        flash('Bookmark not found.', 'error')
        return _redirect_to_index(username)

    db_manager.execute_update(
        "UPDATE bookmark SET `read` = 1, read_later = 0 WHERE bookmarkID = %s AND userID = %s",
        (bookmark_id, user_id),
    )

    flash('Marked as read.', 'success')

    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return _redirect_to_index(username)
