"""
JTTBH Route Decorators
=======================
Three decorators used throughout the application:

    @login_required
        Ensures the user is authenticated.  If not, redirects to the login
        page.  If the URL contains a ``<username>`` segment, verifies it
        matches the session user (admin users bypass this check).

    @permission_required_read(PERM_BIT)
        Verifies that ``session['perm_read'] & perm_bit`` is non-zero.
        Aborts with 403 otherwise.

    @permission_required_write(PERM_BIT)
        Verifies that ``session['perm_write'] & perm_bit`` is non-zero.
        Aborts with 403 otherwise.

Permission bit constants
------------------------
These mirror the values in the database ``permission`` table and are used as
the argument to ``permission_required_read`` / ``permission_required_write``.
"""

import functools

from flask import session, redirect, url_for, abort, request


# ---------------------------------------------------------------------------
# Permission bit constants
# ---------------------------------------------------------------------------

PERM_ADMIN       = 1
PERM_PODCAST     = 2
PERM_APPOINTMENT = 4
PERM_DASHBOARD   = 8
PERM_TODO        = 16
PERM_HABIT       = 32
PERM_PROJECT     = 64
PERM_TRIAGE      = 128
PERM_BOOKMARK    = 256
PERM_FITNESS     = 512
PERM_CHORE       = 1024
PERM_BOOK        = 2048
PERM_JOURNAL     = 4096
PERM_STUDY       = 8192


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

def login_required(f):
    """
    Decorator: require an authenticated session.

    Behaviour
    ---------
    1. If ``session['user_id']`` is absent, redirect to ``/auth/login``.
    2. If the route has a ``<username>`` URL parameter, verify it matches
       ``session['username']``.  Admin users (``perm_read & PERM_ADMIN``)
       are exempt from this check so they can browse any user's pages.
    3. If the username does not match and the user is not an admin, abort
       with 403.

    Usage
    -----
    ::

        @bp.route('/dashboard')
        @login_required
        def dashboard():
            ...
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Must be logged in
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))

        # 2. If the route carries a username segment, validate it
        url_username = kwargs.get('username')
        if url_username is not None:
            session_username = session.get('username', '')
            perm_read = session.get('perm_read', 0)
            is_admin = bool(perm_read & PERM_ADMIN)

            if not is_admin and url_username != session_username:
                abort(403)

        return f(*args, **kwargs)

    return decorated_function


def permission_required_read(perm_bit: int):
    """
    Decorator factory: require a specific read permission bit.

    Parameters
    ----------
    perm_bit : int
        One of the ``PERM_*`` constants defined in this module.

    Returns
    -------
    decorator
        A decorator that aborts with 403 when the session user does not hold
        the requested read permission.

    Usage
    -----
    ::

        @bp.route('/todo')
        @login_required
        @permission_required_read(PERM_TODO)
        def todo_index():
            ...
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            perm_read = session.get('perm_read', 0)
            if not (perm_read & perm_bit):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required_write(perm_bit: int):
    """
    Decorator factory: require a specific write permission bit.

    Parameters
    ----------
    perm_bit : int
        One of the ``PERM_*`` constants defined in this module.

    Returns
    -------
    decorator
        A decorator that aborts with 403 when the session user does not hold
        the requested write permission.

    Usage
    -----
    ::

        @bp.route('/todo/add', methods=['POST'])
        @login_required
        @permission_required_write(PERM_TODO)
        def todo_add():
            ...
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            perm_write = session.get('perm_write', 0)
            if not (perm_write & perm_bit):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
