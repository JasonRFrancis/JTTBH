"""
Hermes Agent REST API — /api/v1
================================
RESTful endpoints consumed by the Hermes Agent (and any future programmatic
client). All routes except /ping require a valid API key:
    Authorization: Bearer <key>

Endpoints
---------
GET  /api/v1/ping
GET  /api/v1/<username>/todos?date=YYYY-MM-DD
POST /api/v1/<username>/todos
POST /api/v1/<username>/todos/<todo_id>/complete
GET  /api/v1/<username>/bookmarks?read_later=1&tag=recipe&limit=50&offset=0
POST /api/v1/<username>/bookmarks
POST /api/v1/<username>/bookmarks/<bookmark_id>/archive
DELETE /api/v1/<username>/bookmarks/<bookmark_id>
GET  /api/v1/<username>/recipes
POST /api/v1/<username>/recipes

Response envelope
-----------------
Success: {"data": ..., "error": null}
Error:   {"error": "message"}
"""

import json
import uuid
from datetime import date, datetime

from flask import Blueprint, jsonify, request, g

from app.services.api_auth import api_key_required
from app.services.database import db_manager
from app.services.decorators import PERM_TODO, PERM_BOOKMARK, PERM_RECIPE
from app.models.todo_model import TodoModel

api_bp = Blueprint('api', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(data):
    return jsonify({'data': data, 'error': None})


def _err(message, status=400):
    return jsonify({'error': message}), status


def _get_user_id(username: str) -> str | None:
    row = db_manager.execute_one(
        'SELECT userID FROM user WHERE username = %s',
        (username,),
    )
    return row['userID'] if row else None


def _require_write(perm_bit: int):
    """Return an error response if the key lacks a write permission bit, else None."""
    if not (g.api_perm_write & perm_bit):
        return _err('Write permission denied', 403)
    return None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@api_bp.route('/ping')
def ping():
    return _ok({'status': 'ok', 'timestamp': datetime.utcnow().isoformat() + 'Z'})


# ---------------------------------------------------------------------------
# Todos
# ---------------------------------------------------------------------------

@api_bp.route('/<username>/todos', methods=['GET'])
@api_key_required
def get_todos(username):
    user_id = _get_user_id(username)
    if not user_id:
        return _err('User not found', 404)

    date_str = request.args.get('date', date.today().isoformat())
    try:
        for_date = date.fromisoformat(date_str)
    except ValueError:
        return _err('Invalid date — use YYYY-MM-DD')

    todos = TodoModel.get_daily_todos(user_id, for_date)
    # Serialize date/datetime fields
    for t in todos:
        if isinstance(t.get('due'), date):
            t['due'] = t['due'].isoformat()
        if isinstance(t.get('added'), date):
            t['added'] = t['added'].isoformat()
        if isinstance(t.get('completed'), datetime):
            t['completed'] = t['completed'].isoformat()

    return _ok({'date': date_str, 'todos': todos})


@api_bp.route('/<username>/todos', methods=['POST'])
@api_key_required
def create_todo(username):
    err = _require_write(PERM_TODO)
    if err:
        return err

    user_id = _get_user_id(username)
    if not user_id:
        return _err('User not found', 404)

    body = request.get_json(silent=True) or {}
    title = (body.get('title') or '').strip()
    if not title:
        return _err('title is required')

    due_str   = body.get('due')
    list_type = body.get('list_type', 'daily')
    list_name = body.get('list_name') or None
    content   = body.get('content') or None

    due = None
    if due_str:
        try:
            due = date.fromisoformat(due_str)
        except ValueError:
            return _err('Invalid due date — use YYYY-MM-DD')

    if list_type == 'daily' and due is None:
        due = date.today()

    todo_id = TodoModel.create(
        user_id=user_id,
        title=title,
        due=due,
        list_type=list_type,
        list_name=list_name,
        content=content,
    )
    return _ok({'todo_id': todo_id}), 201


@api_bp.route('/<username>/todos/<todo_id>/complete', methods=['POST'])
@api_key_required
def complete_todo(username, todo_id):
    err = _require_write(PERM_TODO)
    if err:
        return err

    user_id = _get_user_id(username)
    if not user_id:
        return _err('User not found', 404)

    todo = TodoModel.get_todo_by_id(todo_id, user_id)
    if not todo:
        return _err('Todo not found', 404)

    TodoModel.toggle_complete(todo_id, user_id)
    updated = TodoModel.get_todo_by_id(todo_id, user_id)
    completed_val = updated.get('completed')
    if isinstance(completed_val, datetime):
        completed_val = completed_val.isoformat()

    return _ok({'todo_id': todo_id, 'completed': completed_val})


# ---------------------------------------------------------------------------
# Bookmarks
# ---------------------------------------------------------------------------

@api_bp.route('/<username>/bookmarks', methods=['GET'])
@api_key_required
def get_bookmarks(username):
    user_id = _get_user_id(username)
    if not user_id:
        return _err('User not found', 404)

    conditions = ['b.userID = %s', 'b.`read` = 0']
    params = [user_id]

    if request.args.get('read_later') == '1':
        conditions.append('b.read_later = 1')

    tag = request.args.get('tag', '').strip()
    if tag:
        conditions.append('FIND_IN_SET(%s, REPLACE(b.tags, ", ", ","))')
        params.append(tag)

    try:
        limit  = max(1, min(200, int(request.args.get('limit',  50))))
        offset = max(0, int(request.args.get('offset', 0)))
    except ValueError:
        return _err('limit and offset must be integers')

    where = ' AND '.join(conditions)

    # Total count
    count_row = db_manager.execute_one(
        f'SELECT COUNT(*) AS total FROM bookmark b WHERE {where}',
        tuple(params),
    )
    total = count_row['total'] if count_row else 0

    rows = db_manager.execute_query(
        f'SELECT b.bookmarkID, b.url, b.title, b.description, b.tags, '
        f'b.notes, b.summary, b.read_later, b.created '
        f'FROM bookmark b WHERE {where} ORDER BY b.created DESC '
        f'LIMIT %s OFFSET %s',
        tuple(params) + (limit, offset),
    )

    for r in rows:
        if isinstance(r.get('created'), datetime):
            r['created'] = r['created'].isoformat()

    return _ok({'bookmarks': rows, 'total': total, 'limit': limit, 'offset': offset})


@api_bp.route('/<username>/bookmarks', methods=['POST'])
@api_key_required
def create_bookmark(username):
    err = _require_write(PERM_BOOKMARK)
    if err:
        return err

    user_id = _get_user_id(username)
    if not user_id:
        return _err('User not found', 404)

    body = request.get_json(silent=True) or {}
    url  = (body.get('url') or '').strip()
    if not url:
        return _err('url is required')

    title       = (body.get('title') or '').strip() or url
    description = (body.get('description') or '').strip() or None
    tags        = (body.get('tags') or '').strip() or None
    notes       = (body.get('notes') or '').strip() or None
    read_later  = 1 if body.get('read_later') else 0

    bookmark_id = str(uuid.uuid4())
    db_manager.execute_insert(
        '''INSERT INTO bookmark
               (bookmarkID, userID, url, title, description, tags, notes,
                read_later, `read`, created, created_by)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, NOW(), %s)''',
        (bookmark_id, user_id, url, title, description, tags, notes, read_later, user_id),
    )
    return _ok({'bookmark_id': bookmark_id}), 201


@api_bp.route('/<username>/bookmarks/<bookmark_id>/summary', methods=['PUT'])
@api_key_required
def set_bookmark_summary(username, bookmark_id):
    err = _require_write(PERM_BOOKMARK)
    if err:
        return err

    user_id = _get_user_id(username)
    if not user_id:
        return _err('User not found', 404)

    body = request.get_json(silent=True) or {}
    content = (body.get('content') or '').strip()
    if not content:
        return _err('content is required')

    affected = db_manager.execute_update(
        'UPDATE bookmark SET summary = %s WHERE bookmarkID = %s AND userID = %s',
        (content, bookmark_id, user_id),
    )
    if not affected:
        return _err('Bookmark not found', 404)

    return _ok({'bookmark_id': bookmark_id, 'saved': True})


@api_bp.route('/<username>/bookmarks/<bookmark_id>/archive', methods=['POST'])
@api_key_required
def archive_bookmark(username, bookmark_id):
    err = _require_write(PERM_BOOKMARK)
    if err:
        return err

    user_id = _get_user_id(username)
    if not user_id:
        return _err('User not found', 404)

    affected = db_manager.execute_update(
        'UPDATE bookmark SET `read` = 1 WHERE bookmarkID = %s AND userID = %s',
        (bookmark_id, user_id),
    )
    if not affected:
        return _err('Bookmark not found', 404)

    return _ok({'bookmark_id': bookmark_id, 'archived': True})


@api_bp.route('/<username>/bookmarks/<bookmark_id>', methods=['DELETE'])
@api_key_required
def delete_bookmark(username, bookmark_id):
    err = _require_write(PERM_BOOKMARK)
    if err:
        return err

    user_id = _get_user_id(username)
    if not user_id:
        return _err('User not found', 404)

    affected = db_manager.execute_update(
        'DELETE FROM bookmark WHERE bookmarkID = %s AND userID = %s',
        (bookmark_id, user_id),
    )
    if not affected:
        return _err('Bookmark not found', 404)

    return _ok({'bookmark_id': bookmark_id, 'deleted': True})


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

@api_bp.route('/<username>/recipes', methods=['GET'])
@api_key_required
def get_recipes(username):
    user_id = _get_user_id(username)
    if not user_id:
        return _err('User not found', 404)

    rows = db_manager.execute_query(
        '''SELECT recipeID, title, source, type, servings, prep_time, cook_time,
                  ingredients, directions, notes, created
           FROM recipe
           WHERE userID = %s AND title IS NOT NULL
           ORDER BY created DESC''',
        (user_id,),
    )
    for r in rows:
        if isinstance(r.get('created'), datetime):
            r['created'] = r['created'].isoformat()
        # Parse stored JSON lists
        for field in ('ingredients', 'directions'):
            if r.get(field):
                try:
                    r[field] = json.loads(r[field])
                except (json.JSONDecodeError, TypeError):
                    pass
    return _ok({'recipes': rows})


@api_bp.route('/<username>/recipes', methods=['POST'])
@api_key_required
def create_recipe(username):
    err = _require_write(PERM_RECIPE)
    if err:
        return err

    user_id = _get_user_id(username)
    if not user_id:
        return _err('User not found', 404)

    body = request.get_json(silent=True) or {}
    title = (body.get('title') or '').strip()
    if not title:
        return _err('title is required')

    recipe_id = str(uuid.uuid4())
    ingredients = json.dumps(body.get('ingredients') or [])
    directions  = json.dumps(body.get('directions') or [])

    db_manager.execute_insert(
        '''INSERT INTO recipe
               (recipeID, userID, title, source, type, servings,
                prep_time, cook_time, ingredients, directions, notes,
                position, created, created_by)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, NOW(), %s)''',
        (
            recipe_id, user_id, title,
            body.get('source') or None,
            body.get('type') or None,
            body.get('servings') or None,
            body.get('prep_time') or None,
            body.get('cook_time') or None,
            ingredients, directions,
            body.get('notes') or None,
            user_id,
        ),
    )
    return _ok({'recipe_id': recipe_id}), 201
