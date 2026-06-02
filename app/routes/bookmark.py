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

import secrets
import uuid
from collections import defaultdict
from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
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


def _get_api_token(user_id: str) -> str | None:
    row = db_manager.execute_one(
        "SELECT value FROM user_preference WHERE userID = %s AND preference = 'api_token' ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    return row['value'] if row else None


def _create_api_token(user_id: str) -> str:
    token = secrets.token_hex(32)
    db_manager.execute_insert(
        "INSERT INTO user_preference (userID, preference, value, created, created_by) VALUES (%s, 'api_token', %s, NOW(), %s)",
        (user_id, token, user_id),
    )
    return token


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
    if request.form.get('popup') == '1':
        return redirect(url_for('bookmark.added', username=username))
    return _redirect_to_index(username)


@bookmark_bp.route('/add')
@login_required
@permission_required_read(PERM_BOOKMARK)
def add(username: str):
    """Popup form pre-filled from URL query params (used by bookmarklet)."""
    return render_template(
        'bookmark_add.html',
        username=username,
        url=request.args.get('url', ''),
        title=request.args.get('title', ''),
    )


@bookmark_bp.route('/added')
@login_required
def added(username: str):
    """Shown after a bookmarklet save — tells the popup to close itself."""
    return render_template('bookmark_added.html', username=username)


@bookmark_bp.route('/settings')
@login_required
@permission_required_read(PERM_BOOKMARK)
def settings(username: str):
    user_id = session['user_id']
    token = _get_api_token(user_id)
    bookmarklet = (
        "javascript:(function(){{"
        "var u=encodeURIComponent(location.href);"
        "var t=encodeURIComponent(document.title);"
        "window.open('https://jttbh.com/{username}/bookmark/add?url='+u+'&title='+t,"
        "'jttbh_bm','width=620,height=480,menubar=no,toolbar=no,scrollbars=yes');"
        "}})();"
    ).format(username=username)
    return render_template(
        'bookmark_settings.html',
        username=username,
        token=token,
        bookmarklet=bookmarklet,
    )


@bookmark_bp.route('/token/regenerate/post', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def token_regenerate(username: str):
    _create_api_token(session['user_id'])
    flash('API token regenerated.', 'success')
    return redirect(url_for('bookmark.settings', username=username))


@bookmark_bp.route('/api/create', methods=['POST'])
def api_create(username: str):
    """Token-authenticated JSON endpoint — no session required."""
    token = request.form.get('token', '').strip()
    if not token:
        return jsonify({'status': 'error', 'message': 'Missing token'}), 401

    user = db_manager.execute_one(
        "SELECT userID FROM user WHERE username = %s AND active = 1 AND approval_status = 'approved'",
        (username,),
    )
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    stored = _get_api_token(user['userID'])
    if not stored or stored != token:
        return jsonify({'status': 'error', 'message': 'Invalid token'}), 401

    url = request.form.get('url', '').strip()
    if not url:
        return jsonify({'status': 'error', 'message': 'url is required'}), 400

    title       = request.form.get('title', '').strip() or None
    description = request.form.get('description', '').strip() or None
    tags        = request.form.get('tags', '').strip() or None
    notes       = request.form.get('notes', '').strip() or None
    read_later  = 1 if request.form.get('read_later') in ('1', 'true') else 0

    bookmark_id = str(uuid.uuid4())
    db_manager.execute_insert(
        """INSERT INTO bookmark
               (bookmarkID, userID, url, title, description, tags,
                read_later, `read`, notes, favicon, created, created_by)
           VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, NULL, %s, %s)""",
        (bookmark_id, user['userID'], url, title, description, tags,
         read_later, notes, datetime.now(), user['userID']),
    )
    return jsonify({'status': 'ok', 'bookmarkID': bookmark_id})


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


# ---------------------------------------------------------------------------
# API import (no session required — authenticated by IMPORT_API_KEY header)
# ---------------------------------------------------------------------------

@bookmark_bp.route('/import/post', methods=['POST'])
def bookmark_import(username: str):
    """
    Bulk-import bookmarks from an external script (e.g. Safari tab importer).

    Authentication: X-Api-Key header must match IMPORT_API_KEY in app config.
    Body: JSON array of {url, title} objects.
    Returns: JSON {imported: N, skipped: N, errors: N}
    """
    expected_key = current_app.config.get('IMPORT_API_KEY', '')
    if not expected_key or request.headers.get('X-Api-Key', '') != expected_key:
        return jsonify({'error': 'Unauthorized'}), 401

    user = db_manager.execute_one(
        "SELECT userID FROM `user` WHERE username = %s AND active = 1", (username,)
    )
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user_id = user['userID']

    items = request.get_json(silent=True)
    if not isinstance(items, list):
        return jsonify({'error': 'Expected a JSON array'}), 400

    imported = skipped = errors = 0
    for item in items:
        url   = (item.get('url')   or '').strip()
        title = (item.get('title') or url).strip()[:500]
        if not url or not url.startswith(('http://', 'https://')):
            errors += 1
            continue
        existing = db_manager.execute_one(
            "SELECT id FROM bookmark WHERE userID = %s AND url = %s AND `read` = 0 LIMIT 1",
            (user_id, url),
        )
        if existing:
            skipped += 1
            continue
        db_manager.execute_insert(
            "INSERT INTO bookmark (bookmarkID, userID, url, title, read_later, `read`, created, created_by) "
            "VALUES (%s, %s, %s, %s, 1, 0, NOW(), %s)",
            (str(uuid.uuid4()), user_id, url, title, user_id),
        )
        imported += 1

    return jsonify({'imported': imported, 'skipped': skipped, 'errors': errors})
