"""
Bookmark Routes
===============
Flask blueprint for bookmark management.

URL patterns
------------
GET  /<username>/bookmark/index
GET  /<username>/bookmark/archive
GET  /<username>/bookmark/read-later
GET  /<username>/bookmark/category/<category_id>

POST /<username>/bookmark/create/post
POST /<username>/bookmark/update/post/<bookmark_id>
POST /<username>/bookmark/archive/post/<bookmark_id>   (JSON)
POST /<username>/bookmark/favorite/post/<bookmark_id>  (JSON)
POST /<username>/bookmark/delete/post/<bookmark_id>
POST /<username>/bookmark/delete/bulk/post
POST /<username>/bookmark/read/post/<bookmark_id>      (kept for compatibility)

POST /<username>/bookmark/category/create/post
POST /<username>/bookmark/category/update/post/<category_id>
POST /<username>/bookmark/category/delete/post/<category_id>
POST /<username>/bookmark/category/reorder/post        (JSON)
POST /<username>/bookmark/category/item/add/post/<category_id>    (JSON)
POST /<username>/bookmark/category/item/remove/post/<category_id>/<bookmark_id> (JSON)
POST /<username>/bookmark/category/item/reorder/post/<category_id> (JSON)
"""

import json
import secrets
import re
import uuid
from datetime import datetime

import re

_UNREAD_COUNT_RE = re.compile(r'^\(\d+\)\s*')

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

PER_PAGE = 50


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

_BOOKMARK_BY_ID_SQL = """
    SELECT bookmarkID, url, title, description, tags, favorite, read_later, `read`, notes, favicon
    FROM bookmark
    WHERE bookmarkID = %s AND userID = %s
"""

_CATEGORY_BY_ID_SQL = """
    SELECT categoryID, name, criteria, position
    FROM bookmark_category
    WHERE categoryID = %s AND userID = %s
"""

_CAT_ITEMS_BASE = """
    SELECT b.bookmarkID, b.url, b.title, b.tags, b.favorite, b.notes,
           b.summary, bci.position
    FROM bookmark_category_item bci
    JOIN bookmark b ON b.bookmarkID = bci.bookmarkID
    WHERE bci.categoryID = %s AND b.userID = %s AND b.`read` = 0
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _redirect_to_index(username: str):
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
    return db_manager.execute_one(_BOOKMARK_BY_ID_SQL, (bookmark_id, user_id))


def _normalise_tags(raw: str) -> str | None:
    """Strip spaces from each tag; deduplicate; return None if empty."""
    parts = [p.replace(' ', '').strip(',') for p in raw.split(',') if p.strip()]
    seen = []
    for p in parts:
        if p and p not in seen:
            seen.append(p)
    return ','.join(seen) or None


def _get_category(category_id: str, user_id: str) -> dict | None:
    return db_manager.execute_one(_CATEGORY_BY_ID_SQL, (category_id, user_id))


def _apply_criteria(user_id: str, category_id: str, criteria: dict) -> int:
    """Auto-assign matching bookmarks to a category. Returns count added."""
    pattern = criteria.get('url_contains', '').strip()
    if not pattern:
        return 0

    max_row = db_manager.execute_one(
        "SELECT COALESCE(MAX(position), -1) AS max_pos FROM bookmark_category_item WHERE categoryID = %s",
        (category_id,),
    )
    next_pos = (max_row['max_pos'] + 1) if max_row else 0

    matches = db_manager.execute_query(
        """SELECT b.bookmarkID FROM bookmark b
           WHERE b.userID = %s AND b.`read` = 0
             AND b.url LIKE %s
             AND b.bookmarkID NOT IN (
                 SELECT bookmarkID FROM bookmark_category_item WHERE categoryID = %s
             )""",
        (user_id, f'%{pattern}%', category_id),
    )

    added = 0
    for row in matches:
        db_manager.execute_insert(
            "INSERT INTO bookmark_category_item (categoryID, bookmarkID, userID, position, created, created_by) "
            "VALUES (%s, %s, %s, %s, NOW(), %s)",
            (category_id, row['bookmarkID'], user_id, next_pos, user_id),
        )
        next_pos += 1
        added += 1

    return added


def _auto_assign_new_bookmark(user_id: str, bookmark_id: str, url: str) -> None:
    """Check all categories with criteria; auto-add new bookmark if it matches."""
    cats = db_manager.execute_query(
        "SELECT categoryID, criteria FROM bookmark_category WHERE userID = %s AND criteria IS NOT NULL",
        (user_id,),
    )
    for cat in cats:
        try:
            criteria = json.loads(cat['criteria'])
        except (ValueError, TypeError):
            continue
        pattern = criteria.get('url_contains', '').strip()
        if not pattern or pattern.lower() not in url.lower():
            continue
        max_row = db_manager.execute_one(
            "SELECT COALESCE(MAX(position), -1) AS max_pos FROM bookmark_category_item WHERE categoryID = %s",
            (cat['categoryID'],),
        )
        next_pos = (max_row['max_pos'] + 1) if max_row else 0
        try:
            db_manager.execute_insert(
                "INSERT INTO bookmark_category_item (categoryID, bookmarkID, userID, position, created, created_by) "
                "VALUES (%s, %s, %s, %s, NOW(), %s)",
                (cat['categoryID'], bookmark_id, user_id, next_pos, user_id),
            )
        except Exception:
            pass  # UNIQUE constraint — already assigned


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@bookmark_bp.route('/index')
@login_required
@permission_required_read(PERM_BOOKMARK)
def index(username: str):
    user_id = session['user_id']

    categories = db_manager.execute_query(
        "SELECT categoryID, name, criteria, position FROM bookmark_category "
        "WHERE userID = %s ORDER BY position",
        (user_id,),
    )

    for cat in categories:
        items = db_manager.execute_query(
            _CAT_ITEMS_BASE + " ORDER BY bci.position LIMIT %s",
            (cat['categoryID'], user_id, PER_PAGE),
        )
        total_row = db_manager.execute_one(
            "SELECT COUNT(*) AS cnt FROM bookmark_category_item bci "
            "JOIN bookmark b ON b.bookmarkID = bci.bookmarkID "
            "WHERE bci.categoryID = %s AND b.userID = %s AND b.`read` = 0",
            (cat['categoryID'], user_id),
        )
        cat['bm_list'] = items
        cat['total'] = total_row['cnt'] if total_row else 0
        try:
            cat['criteria_url'] = json.loads(cat['criteria'] or '{}').get('url_contains', '')
        except (ValueError, TypeError):
            cat['criteria_url'] = ''

    # Favorites: active bookmarks with favorite=1, newest first
    favorites = db_manager.execute_query(
        """SELECT b.bookmarkID, b.url, b.title, b.tags, b.favorite, b.notes, b.summary
           FROM bookmark b
           WHERE b.userID = %s AND b.`read` = 0 AND b.favorite = 1
           ORDER BY b.created DESC
           LIMIT %s""",
        (user_id, PER_PAGE + 1),
    )
    fav_has_more = len(favorites) > PER_PAGE
    if fav_has_more:
        favorites = favorites[:PER_PAGE]
    fav_total_row = db_manager.execute_one(
        "SELECT COUNT(*) AS cnt FROM bookmark WHERE userID = %s AND `read` = 0 AND favorite = 1",
        (user_id,),
    )
    fav_total = fav_total_row['cnt'] if fav_total_row else 0

    # Uncategorized: active bookmarks not in any category_item for this user
    uncategorized = db_manager.execute_query(
        """SELECT b.bookmarkID, b.url, b.title, b.tags, b.favorite, b.notes, b.summary
           FROM bookmark b
           WHERE b.userID = %s AND b.`read` = 0
             AND b.bookmarkID NOT IN (
                 SELECT bci.bookmarkID FROM bookmark_category_item bci WHERE bci.userID = %s
             )
           ORDER BY b.created DESC
           LIMIT %s""",
        (user_id, user_id, PER_PAGE + 1),
    )
    uncat_has_more = len(uncategorized) > PER_PAGE
    if uncat_has_more:
        uncategorized = uncategorized[:PER_PAGE]

    uncat_total_row = db_manager.execute_one(
        """SELECT COUNT(*) AS cnt FROM bookmark b
           WHERE b.userID = %s AND b.`read` = 0
             AND b.bookmarkID NOT IN (
                 SELECT bci.bookmarkID FROM bookmark_category_item bci WHERE bci.userID = %s
             )""",
        (user_id, user_id),
    )
    uncat_total = uncat_total_row['cnt'] if uncat_total_row else 0

    return render_template(
        'bookmark_index.html',
        username=username,
        categories=categories,
        favorites=favorites,
        fav_total=fav_total,
        uncategorized=uncategorized,
        uncat_total=uncat_total,
    )


_SORT_ORDER = {
    'date_desc':  'b.created DESC',
    'date_asc':   'b.created ASC',
    'title_asc':  'b.title ASC',
    'title_desc': 'b.title DESC',
    'domain_asc': 'SUBSTRING_INDEX(SUBSTRING_INDEX(b.url, "/", 3), "//", -1) ASC',
    'manual':     'bci.position ASC',
}


@bookmark_bp.route('/items/json')
@login_required
@permission_required_read(PERM_BOOKMARK)
def items_json(username: str):
    """Return a sorted list of bookmark items for a card as JSON.

    Query params
    ------------
    cat  : category UUID | '__favorites__' | '__uncat__'
    sort : date_desc | date_asc | title_asc | title_desc | domain_asc | manual
    """
    user_id = session['user_id']
    cat     = request.args.get('cat', '').strip()
    sort    = request.args.get('sort', 'date_desc')
    order   = _SORT_ORDER.get(sort, 'b.created DESC')

    cols = 'b.bookmarkID, b.url, b.title, b.tags, b.favorite, b.notes'

    if cat == '__favorites__':
        if sort == 'manual':
            order = 'b.created DESC'
        rows = db_manager.execute_query(
            f'SELECT {cols} FROM bookmark b '
            f'WHERE b.userID = %s AND b.`read` = 0 AND b.favorite = 1 '
            f'ORDER BY {order}',
            (user_id,),
        )
    elif cat == '__uncat__':
        if sort == 'manual':
            order = 'b.created DESC'
        rows = db_manager.execute_query(
            f'SELECT {cols} FROM bookmark b '
            f'WHERE b.userID = %s AND b.`read` = 0 '
            f'AND b.bookmarkID NOT IN ('
            f'  SELECT bci.bookmarkID FROM bookmark_category_item bci WHERE bci.userID = %s'
            f') ORDER BY {order}',
            (user_id, user_id),
        )
    else:
        cat_row = _get_category(cat, user_id)
        if not cat_row:
            return jsonify({'error': 'Not found'}), 404
        rows = db_manager.execute_query(
            f'SELECT {cols}, bci.position FROM bookmark_category_item bci '
            f'JOIN bookmark b ON b.bookmarkID = bci.bookmarkID '
            f'WHERE bci.categoryID = %s AND b.userID = %s AND b.`read` = 0 '
            f'ORDER BY {order}',
            (cat, user_id),
        )

    return jsonify({'items': [dict(r) for r in rows]})


@bookmark_bp.route('/recent')
@login_required
@permission_required_read(PERM_BOOKMARK)
def recent(username: str):
    from datetime import timedelta
    user_id = session['user_id']
    cutoff = datetime.now() - timedelta(hours=24)

    bookmarks = db_manager.execute_query(
        """SELECT bookmarkID, url, title, tags, favorite, read_later, notes, created
           FROM bookmark
           WHERE userID = %s AND `read` = 0 AND created >= %s
           ORDER BY created DESC
           LIMIT 100""",
        (user_id, cutoff)
    )

    favorites = db_manager.execute_query(
        """SELECT bookmarkID, url, title, tags, favorite, read_later, notes, created
           FROM bookmark
           WHERE userID = %s AND `read` = 0 AND favorite = 1 AND created < %s
           ORDER BY created DESC
           LIMIT 20""",
        (user_id, cutoff)
    )

    def classify(bm):
        url = bm['url'].lower()
        if any(x in url for x in ('youtube.com', 'youtu.be', 'vimeo.com', 'twitch.tv')):
            return 'Videos'
        if bm.get('read_later'):
            return 'Read Later'
        if any(x in url for x in ('twitter.com', 'x.com', 'reddit.com', 'facebook.com', 'instagram.com')):
            return 'Social'
        return 'Articles'

    groups = {}
    for bm in bookmarks:
        cat = classify(bm)
        groups.setdefault(cat, []).append(bm)

    return render_template(
        'bookmark_recent.html',
        username=username,
        groups=groups,
        favorites=favorites,
    )


@bookmark_bp.route('/archive')
@login_required
@permission_required_read(PERM_BOOKMARK)
def archive(username: str):
    user_id = session['user_id']
    items = db_manager.execute_query(
        "SELECT bookmarkID, url, title, tags, favorite, created "
        "FROM bookmark WHERE userID = %s AND `read` = 1 "
        "ORDER BY created DESC",
        (user_id,),
    )
    return render_template('bookmark_archive.html', username=username, items=items)


@bookmark_bp.route('/read-later')
@login_required
@permission_required_read(PERM_BOOKMARK)
def read_later(username: str):
    user_id = session['user_id']
    bookmarks = db_manager.execute_query(
        """SELECT bookmarkID, url, title, description, tags, read_later, `read`, notes, favicon,
                  DATE(created) AS created_date
           FROM bookmark
           WHERE userID = %s AND read_later = 1 AND `read` = 0
           ORDER BY created DESC""",
        (user_id,),
    )
    return render_template('bookmark_read_later.html', bookmarks=bookmarks, username=username)


@bookmark_bp.route('/category/<category_id>')
@login_required
@permission_required_read(PERM_BOOKMARK)
def category_view(username: str, category_id: str):
    user_id = session['user_id']
    category = _get_category(category_id, user_id)
    if not category:
        flash('Category not found.', 'error')
        return _redirect_to_index(username)

    page = max(1, int(request.args.get('page', 1) or 1))
    q    = request.args.get('q', '').strip()
    offset = (page - 1) * PER_PAGE

    if q:
        like = f'%{q}%'
        items = db_manager.execute_query(
            _CAT_ITEMS_BASE + " AND (b.title LIKE %s OR b.url LIKE %s)"
            " ORDER BY bci.position LIMIT %s OFFSET %s",
            (category_id, user_id, like, like, PER_PAGE, offset),
        )
        total_row = db_manager.execute_one(
            "SELECT COUNT(*) AS cnt FROM bookmark_category_item bci "
            "JOIN bookmark b ON b.bookmarkID = bci.bookmarkID "
            "WHERE bci.categoryID = %s AND b.userID = %s AND b.`read` = 0 "
            "AND (b.title LIKE %s OR b.url LIKE %s)",
            (category_id, user_id, like, like),
        )
    else:
        items = db_manager.execute_query(
            _CAT_ITEMS_BASE + " ORDER BY bci.position LIMIT %s OFFSET %s",
            (category_id, user_id, PER_PAGE, offset),
        )
        total_row = db_manager.execute_one(
            "SELECT COUNT(*) AS cnt FROM bookmark_category_item bci "
            "JOIN bookmark b ON b.bookmarkID = bci.bookmarkID "
            "WHERE bci.categoryID = %s AND b.userID = %s AND b.`read` = 0",
            (category_id, user_id),
        )

    total = total_row['cnt'] if total_row else 0
    pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)

    return render_template(
        'bookmark_category.html',
        username=username,
        category=category,
        items=items,
        page=page,
        pages=pages,
        total=total,
        q=q,
    )


# ---------------------------------------------------------------------------
# Bookmark POST routes
# ---------------------------------------------------------------------------

@bookmark_bp.route('/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def create(username: str):
    user_id = session['user_id']
    url = request.form.get('url', '').strip()

    if not url:
        flash('URL is required.', 'error')
        return _redirect_to_index(username)

    title       = _UNREAD_COUNT_RE.sub('', request.form.get('title', '').strip()) or None
    description = request.form.get('description', '').strip() or None
    tags        = _normalise_tags(request.form.get('tags', ''))
    notes       = request.form.get('notes', '').strip() or None
    read_later  = 1 if request.form.get('read_later') == '1' else 0

    bookmark_id = str(uuid.uuid4())
    db_manager.execute_insert(
        """INSERT INTO bookmark
               (bookmarkID, userID, url, title, description, tags, read_later, `read`, notes, favicon, created, created_by)
           VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, NULL, %s, %s)""",
        (bookmark_id, user_id, url, title, description, tags,
         read_later, notes, datetime.now(), user_id),
    )
    _auto_assign_new_bookmark(user_id, bookmark_id, url)

    flash('Bookmark added.', 'success')
    if request.form.get('popup') == '1':
        return redirect(url_for('bookmark.added', username=username))
    return _redirect_to_index(username)


@bookmark_bp.route('/update/post/<bookmark_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def update(username: str, bookmark_id: str):
    user_id = session['user_id']
    bm = _get_bookmark(bookmark_id, user_id)
    if not bm:
        return jsonify({'status': 'error', 'message': 'Not found'}), 404

    title = _UNREAD_COUNT_RE.sub('', request.form.get('title', '').strip()) or bm['title']
    tags  = _normalise_tags(request.form.get('tags', ''))
    notes = request.form.get('notes', '').strip() or None

    db_manager.execute_update(
        "UPDATE bookmark SET title = %s, tags = %s, notes = %s WHERE bookmarkID = %s AND userID = %s",
        (title, tags, notes, bookmark_id, user_id),
    )
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return jsonify({'status': 'ok', 'title': title})
    flash('Bookmark updated.', 'success')
    return redirect(request.referrer or url_for('bookmark.index', username=username))


@bookmark_bp.route('/archive/post/<bookmark_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def toggle_archive(username: str, bookmark_id: str):
    user_id = session['user_id']
    bm = _get_bookmark(bookmark_id, user_id)
    if not bm:
        return jsonify({'status': 'error', 'message': 'Not found'}), 404

    new_val = 0 if bm['read'] else 1
    db_manager.execute_update(
        "UPDATE bookmark SET `read` = %s WHERE bookmarkID = %s AND userID = %s",
        (new_val, bookmark_id, user_id),
    )
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return jsonify({'status': 'ok', 'archived': bool(new_val)})
    flash('Bookmark archived.' if new_val else 'Bookmark restored.', 'success')
    return redirect(request.referrer or url_for('bookmark.index', username=username))


@bookmark_bp.route('/favorite/post/<bookmark_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def toggle_favorite(username: str, bookmark_id: str):
    user_id = session['user_id']
    bm = _get_bookmark(bookmark_id, user_id)
    if not bm:
        return jsonify({'status': 'error', 'message': 'Not found'}), 404

    new_val = 0 if bm['favorite'] else 1
    db_manager.execute_update(
        "UPDATE bookmark SET favorite = %s WHERE bookmarkID = %s AND userID = %s",
        (new_val, bookmark_id, user_id),
    )
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return jsonify({'status': 'ok', 'favorite': bool(new_val)})
    flash('Favorited.' if new_val else 'Unfavorited.', 'success')
    return redirect(request.referrer or url_for('bookmark.index', username=username))


@bookmark_bp.route('/delete/post/<bookmark_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def delete(username: str, bookmark_id: str):
    user_id = session['user_id']
    bm = _get_bookmark(bookmark_id, user_id)
    if not bm:
        flash('Bookmark not found.', 'error')
        return redirect(request.referrer or url_for('bookmark.archive', username=username))

    db_manager.execute_update(
        "DELETE FROM bookmark WHERE bookmarkID = %s AND userID = %s",
        (bookmark_id, user_id),
    )
    flash('Bookmark deleted.', 'success')
    return redirect(request.referrer or url_for('bookmark.archive', username=username))


@bookmark_bp.route('/delete/bulk/post', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def delete_bulk(username: str):
    user_id   = session['user_id']
    bm_ids    = request.form.getlist('bookmark_id')
    deleted   = 0
    for bm_id in bm_ids:
        rows = db_manager.execute_update(
            "DELETE FROM bookmark WHERE bookmarkID = %s AND userID = %s",
            (bm_id, user_id),
        )
        deleted += rows
    flash(f'{deleted} bookmark(s) deleted.', 'success')
    return redirect(url_for('bookmark.archive', username=username))


@bookmark_bp.route('/read/post/<bookmark_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def mark_read(username: str, bookmark_id: str):
    """Kept for backward compatibility — marks as archived."""
    user_id = session['user_id']
    db_manager.execute_update(
        "UPDATE bookmark SET `read` = 1, read_later = 0 WHERE bookmarkID = %s AND userID = %s",
        (bookmark_id, user_id),
    )
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return _redirect_to_index(username)


# ---------------------------------------------------------------------------
# Category POST routes
# ---------------------------------------------------------------------------

@bookmark_bp.route('/category/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def category_create(username: str):
    user_id = session['user_id']
    name    = request.form.get('name', '').strip()
    if not name:
        flash('Category name is required.', 'error')
        return _redirect_to_index(username)

    criteria_str = request.form.get('url_contains', '').strip()
    criteria     = json.dumps({'url_contains': criteria_str}) if criteria_str else None

    max_row = db_manager.execute_one(
        "SELECT COALESCE(MAX(position), -1) AS max_pos FROM bookmark_category WHERE userID = %s",
        (user_id,),
    )
    position    = (max_row['max_pos'] + 1) if max_row else 0
    category_id = str(uuid.uuid4())

    db_manager.execute_insert(
        "INSERT INTO bookmark_category (categoryID, userID, name, position, criteria, created, created_by) "
        "VALUES (%s, %s, %s, %s, %s, NOW(), %s)",
        (category_id, user_id, name, position, criteria, user_id),
    )

    if criteria_str:
        _apply_criteria(user_id, category_id, {'url_contains': criteria_str})

    flash(f'Category "{name}" created.', 'success')
    return _redirect_to_index(username)


@bookmark_bp.route('/category/update/post/<category_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def category_update(username: str, category_id: str):
    user_id  = session['user_id']
    category = _get_category(category_id, user_id)
    if not category:
        flash('Category not found.', 'error')
        return _redirect_to_index(username)

    name         = request.form.get('name', '').strip() or category['name']
    criteria_str = request.form.get('url_contains', '').strip()
    criteria     = json.dumps({'url_contains': criteria_str}) if criteria_str else None

    db_manager.execute_update(
        "UPDATE bookmark_category SET name = %s, criteria = %s WHERE categoryID = %s AND userID = %s",
        (name, criteria, category_id, user_id),
    )

    try:
        old_criteria = json.loads(category['criteria'] or '{}')
    except (ValueError, TypeError):
        old_criteria = {}

    if criteria_str and criteria_str != old_criteria.get('url_contains', ''):
        _apply_criteria(user_id, category_id, {'url_contains': criteria_str})

    flash(f'Category "{name}" updated.', 'success')
    return _redirect_to_index(username)


@bookmark_bp.route('/category/delete/post/<category_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def category_delete(username: str, category_id: str):
    user_id  = session['user_id']
    category = _get_category(category_id, user_id)
    if not category:
        flash('Category not found.', 'error')
        return _redirect_to_index(username)

    db_manager.execute_update(
        "DELETE FROM bookmark_category WHERE categoryID = %s AND userID = %s",
        (category_id, user_id),
    )
    flash(f'Category "{category["name"]}" deleted.', 'success')
    return _redirect_to_index(username)


@bookmark_bp.route('/category/reorder/post', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def category_reorder(username: str):
    user_id = session['user_id']
    items   = request.get_json(silent=True) or []
    for item in items:
        if not isinstance(item, dict):
            continue
        cat_id = item.get('categoryID')
        pos    = item.get('position')
        if cat_id and pos is not None:
            try:
                db_manager.execute_update(
                    "UPDATE bookmark_category SET position = %s WHERE categoryID = %s AND userID = %s",
                    (int(pos), cat_id, user_id),
                )
            except (ValueError, TypeError):
                pass
    return jsonify({'status': 'ok'})


@bookmark_bp.route('/category/item/add/post/<category_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def category_item_add(username: str, category_id: str):
    user_id     = session['user_id']
    category    = _get_category(category_id, user_id)
    bookmark_id = (request.get_json(silent=True) or {}).get('bookmarkID', '').strip()
    if not category or not bookmark_id:
        return jsonify({'status': 'error'}), 400

    bm = _get_bookmark(bookmark_id, user_id)
    if not bm:
        return jsonify({'status': 'error', 'message': 'Bookmark not found'}), 404

    max_row = db_manager.execute_one(
        "SELECT COALESCE(MAX(position), -1) AS max_pos FROM bookmark_category_item WHERE categoryID = %s",
        (category_id,),
    )
    next_pos = (max_row['max_pos'] + 1) if max_row else 0
    try:
        db_manager.execute_insert(
            "INSERT INTO bookmark_category_item (categoryID, bookmarkID, userID, position, created, created_by) "
            "VALUES (%s, %s, %s, %s, NOW(), %s)",
            (category_id, bookmark_id, user_id, next_pos, user_id),
        )
    except Exception:
        pass  # Already in category
    return jsonify({'status': 'ok'})


@bookmark_bp.route('/category/item/remove/post/<category_id>/<bookmark_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def category_item_remove(username: str, category_id: str, bookmark_id: str):
    user_id = session['user_id']
    db_manager.execute_update(
        "DELETE FROM bookmark_category_item WHERE categoryID = %s AND bookmarkID = %s AND userID = %s",
        (category_id, bookmark_id, user_id),
    )
    return jsonify({'status': 'ok'})


@bookmark_bp.route('/category/item/reorder/post/<category_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def category_item_reorder(username: str, category_id: str):
    user_id  = session['user_id']
    category = _get_category(category_id, user_id)
    if not category:
        return jsonify({'status': 'error'}), 404

    items = request.get_json(silent=True) or []
    for item in items:
        if not isinstance(item, dict):
            continue
        bm_id = item.get('bookmarkID')
        pos   = item.get('position')
        if bm_id and pos is not None:
            try:
                db_manager.execute_update(
                    "UPDATE bookmark_category_item SET position = %s "
                    "WHERE categoryID = %s AND bookmarkID = %s AND userID = %s",
                    (int(pos), category_id, bm_id, user_id),
                )
            except (ValueError, TypeError):
                pass
    return jsonify({'status': 'ok'})


# ---------------------------------------------------------------------------
# Bookmarklet / add form
# ---------------------------------------------------------------------------

@bookmark_bp.route('/quick-save')
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def quick_save(username: str):
    """Quick-save a URL as Read Later without showing a form."""
    user_id = session['user_id']
    url = request.args.get('url', '').strip()
    title = _UNREAD_COUNT_RE.sub('', request.args.get('title', '').strip()) or url[:100]

    if not url:
        flash('No URL provided.', 'error')
        return _redirect_to_index(username)

    # Check for duplicate
    existing = db_manager.execute_one(
        "SELECT bookmarkID FROM bookmark WHERE userID = %s AND url = %s AND `read` = 0 LIMIT 1",
        (user_id, url)
    )
    if existing:
        db_manager.execute_update(
            "UPDATE bookmark SET read_later = 1 WHERE bookmarkID = %s AND userID = %s",
            (existing['bookmarkID'], user_id)
        )
        return render_template('bookmark_added.html', username=username, message='Already saved — marked as Read Later.')

    bookmark_id = str(uuid.uuid4())
    db_manager.execute_insert(
        """INSERT INTO bookmark
               (bookmarkID, userID, url, title, description, tags, read_later, `read`, notes, favicon, created, created_by)
           VALUES (%s, %s, %s, %s, NULL, NULL, 1, 0, NULL, NULL, %s, %s)""",
        (bookmark_id, user_id, url, title or None, datetime.now(), user_id),
    )
    _auto_assign_new_bookmark(user_id, bookmark_id, url)
    return render_template('bookmark_added.html', username=username, message='Saved to Read Later!')


@bookmark_bp.route('/add')
@login_required
@permission_required_read(PERM_BOOKMARK)
def add(username: str):
    """Popup form pre-filled from URL query params (used by bookmarklet)."""
    return render_template(
        'bookmark_add.html',
        username=username,
        url=request.args.get('url', ''),
        title=_UNREAD_COUNT_RE.sub('', request.args.get('title', '')),
    )


@bookmark_bp.route('/added')
@login_required
def added(username: str):
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
        "'jttbh_bm','width=620,height=580,menubar=no,toolbar=no,scrollbars=no');"
        "}})();"
    ).format(username=username)
    quick_bookmarklet = (
        "javascript:(function(){{"
        "var u=encodeURIComponent(location.href);"
        "var t=encodeURIComponent(document.title);"
        "window.open('https://jttbh.com/{username}/bookmark/quick-save?url='+u+'&title='+t,'_blank');"
        "}})();"
    ).format(username=username)
    return render_template(
        'bookmark_settings.html',
        username=username,
        token=token,
        bookmarklet=bookmarklet,
        quick_bookmarklet=quick_bookmarklet,
    )


@bookmark_bp.route('/summary/<bookmark_id>/json')
@login_required
@permission_required_read(PERM_BOOKMARK)
def summary_json(username: str, bookmark_id: str):
    """Generate an AI summary of the bookmarked page using Claude."""
    user_id = session['user_id']
    bm = _get_bookmark(bookmark_id, user_id)
    if not bm:
        return jsonify({'error': 'Not found'}), 404

    url = bm['url']

    # Fetch the page
    try:
        import requests as _req
        resp = _req.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        return jsonify({'error': f'Could not fetch page: {e}'}), 502

    # Extract text
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        text = soup.get_text(separator=' ', strip=True)[:8000]
    except Exception:
        text = html[:8000]

    if not text.strip():
        return jsonify({'error': 'No text content found'}), 422

    # Call Claude
    try:
        import anthropic
        import json as _json
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=800,
            messages=[{
                'role': 'user',
                'content': (
                    f'Summarize this web page in three formats. Respond with ONLY valid JSON, no other text.\n'
                    f'Format: {{"one":"<one sentence>","three":"<three sentences>","long":"<two paragraphs>"}}\n\n'
                    f'Page title: {bm.get("title","")}\nURL: {url}\n\nContent:\n{text}'
                )
            }]
        )
        result = _json.loads(msg.content[0].text)
        db_manager.execute_update(
            'UPDATE bookmark SET summary = %s WHERE bookmarkID = %s AND userID = %s',
            (result.get('long', ''), bookmark_id, user_id),
        )
        return jsonify({'status': 'ok', 'summary': result})
    except Exception as e:
        return jsonify({'error': f'Summary failed: {e}'}), 500


@bookmark_bp.route('/token/regenerate/post', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOKMARK)
@permission_required_write(PERM_BOOKMARK)
def token_regenerate(username: str):
    _create_api_token(session['user_id'])
    flash('API token regenerated.', 'success')
    return redirect(url_for('bookmark.settings', username=username))


# ---------------------------------------------------------------------------
# Token API (external clients)
# ---------------------------------------------------------------------------

@bookmark_bp.route('/api/create', methods=['POST'])
def api_create(username: str):
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

    title      = request.form.get('title', '').strip() or None
    description = request.form.get('description', '').strip() or None
    tags       = request.form.get('tags', '').strip() or None
    notes      = request.form.get('notes', '').strip() or None
    read_later = 1 if request.form.get('read_later') in ('1', 'true') else 0

    bookmark_id = str(uuid.uuid4())
    db_manager.execute_insert(
        """INSERT INTO bookmark
               (bookmarkID, userID, url, title, description, tags,
                read_later, `read`, notes, favicon, created, created_by)
           VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, NULL, %s, %s)""",
        (bookmark_id, user['userID'], url, title, description, tags,
         read_later, notes, datetime.now(), user['userID']),
    )
    _auto_assign_new_bookmark(user['userID'], bookmark_id, url)
    return jsonify({'status': 'ok', 'bookmarkID': bookmark_id})


# ---------------------------------------------------------------------------
# Bulk import API (IMPORT_API_KEY auth)
# ---------------------------------------------------------------------------

@bookmark_bp.route('/import/post', methods=['POST'])
def bookmark_import(username: str):
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
        title = _UNREAD_COUNT_RE.sub('', (item.get('title') or url).strip())[:500]
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
        bookmark_id = str(uuid.uuid4())
        db_manager.execute_insert(
            "INSERT INTO bookmark (bookmarkID, userID, url, title, read_later, `read`, created, created_by) "
            "VALUES (%s, %s, %s, %s, 1, 0, NOW(), %s)",
            (bookmark_id, user_id, url, title, user_id),
        )
        _auto_assign_new_bookmark(user_id, bookmark_id, url)
        imported += 1

    return jsonify({'imported': imported, 'skipped': skipped, 'errors': errors})
