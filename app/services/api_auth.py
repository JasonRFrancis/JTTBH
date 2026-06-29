"""
API Key Authentication
======================
Provides Bearer-token auth for the /api/v1 blueprint.

Table: api_key
    id          INT PK
    keyID       VARCHAR(36) UNIQUE  – UUID for the key row
    userID      VARCHAR(36)         – FK -> user.userID
    key_hash    VARCHAR(128)        – SHA-256 hex of raw bearer token
    key_name    VARCHAR(100)        – Human label
    permissions TEXT                – JSON: {"read": N, "write": N}
    active      TINYINT(1)          – 1 = valid, 0 = revoked
    last_used   DATETIME NULL
    created     DATETIME

Usage
-----
    from app.services.api_auth import api_key_required, generate_key

    # Provisioning (run once via scripts/generate_api_key.py):
    raw_key, key_hash = generate_key()   # store key_hash; show raw_key once

    # Protecting a route:
    @api_bp.route('/<username>/todos')
    @api_key_required
    def get_todos(username):
        user_id = g.api_user_id
        ...

After a successful check the following are available on Flask's g:
    g.api_key_id    – int row id
    g.api_user_id   – str UUID of the key owner (userID)
    g.api_perm_read – int permission bitvector
    g.api_perm_write– int permission bitvector
"""

import hashlib
import json
import secrets
import functools

from flask import request, jsonify, g

from app.services.database import db_manager
from app.services.decorators import PERM_ADMIN

KEY_PREFIX = 'jttbh_'


def generate_key() -> tuple[str, str]:
    """
    Generate a new API key pair.

    Returns
    -------
    tuple[str, str]
        ``(raw_key, key_hash)`` — store only ``key_hash`` in the database.
        The ``raw_key`` must be shown to the user exactly once.
    """
    raw_key  = KEY_PREFIX + secrets.token_hex(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_hash


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _parse_permissions(permissions_json: str | None) -> tuple[int, int]:
    """Parse the permissions JSON field into (perm_read, perm_write)."""
    if not permissions_json:
        return (0, 0)
    try:
        data = json.loads(permissions_json)
        return (int(data.get('read', 0)), int(data.get('write', 0)))
    except (json.JSONDecodeError, TypeError, ValueError):
        return (0, 0)


def api_key_required(f):
    """
    Decorator: require a valid API key in the Authorization header.

    Expects: ``Authorization: Bearer <raw_key>``

    Checks
    ------
    1. Header present and starts with 'Bearer '.
    2. Key hash found in api_key table and active = 1.
    3. If the route has a <username> segment, the key's owner matches that
       username — unless the key has the PERM_ADMIN bit set.
    4. Updates api_key.last_used on success.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401

        raw_key  = auth_header[7:]
        key_hash = _hash_key(raw_key)

        row = db_manager.execute_one(
            'SELECT * FROM api_key WHERE key_hash = %s AND active = 1',
            (key_hash,),
        )
        if not row:
            return jsonify({'error': 'Invalid or revoked API key'}), 401

        perm_read, perm_write = _parse_permissions(row.get('permissions'))

        # Username ownership check
        url_username = kwargs.get('username')
        if url_username is not None:
            is_admin = bool(perm_read & PERM_ADMIN)
            if not is_admin:
                owner = db_manager.execute_one(
                    'SELECT username FROM user WHERE userID = %s',
                    (row['userID'],),
                )
                if not owner or owner['username'] != url_username:
                    return jsonify({'error': 'Forbidden'}), 403

        # Update last_used (intentional direct UPDATE — api_key is not insert-only)
        db_manager.execute_update(
            'UPDATE api_key SET last_used = NOW() WHERE id = %s',
            (row['id'],),
        )

        g.api_key_id     = row['id']
        g.api_user_id    = row['userID']
        g.api_perm_read  = perm_read
        g.api_perm_write = perm_write

        return f(*args, **kwargs)

    return decorated_function
