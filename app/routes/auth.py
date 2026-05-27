"""
JTTBH Authentication Routes
=============================
Google OAuth 2.0 login flow.

Routes
------
GET  /auth/login              – Render login page with Google Sign-In button.
GET  /auth/oauth2callback     – Handle Google OAuth callback.
GET  /auth/logout             – Clear session and redirect to login.
GET  /pending-approval        – Inform new users their account is pending.

OAuth flow
----------
1. User clicks "Sign in with Google" -> redirected to Google's OAuth consent
   page with scopes: openid, email, profile, gmail.readonly, calendar.readonly.
2. Google redirects back to /auth/oauth2callback with an authorisation code.
3. Exchange code for tokens; fetch user profile from Google.
4. Look up user by google_id in the ``user`` table.
   - Not found  -> create user with approval_status='pending'; redirect to
                   /pending-approval and send admin alert.
   - pending    -> redirect to /pending-approval.
   - rejected   -> flash error; redirect to /auth/login.
   - approved   -> populate session; redirect to /[username]/dashboard/index.
"""

import os
import uuid
import re

from flask import (
    Blueprint,
    redirect,
    url_for,
    request,
    session,
    flash,
    render_template,
    current_app,
)
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow

from app.services.database import db_manager
from app.services.email_service import email_service


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

auth_bp = Blueprint('auth', __name__)


# ---------------------------------------------------------------------------
# OAuth scopes and redirect URI key
# ---------------------------------------------------------------------------

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly',
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_flow() -> Flow:
    """
    Construct a google_auth_oauthlib Flow from app config.

    Requires config keys:
        GOOGLE_CLIENT_ID
        GOOGLE_CLIENT_SECRET
        GOOGLE_REDIRECT_URI   (e.g. 'http://localhost:5000/auth/oauth2callback')
    """
    client_config = {
        'web': {
            'client_id':     current_app.config['GOOGLE_CLIENT_ID'],
            'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
            'auth_uri':      'https://accounts.google.com/o/oauth2/auth',
            'token_uri':     'https://oauth2.googleapis.com/token',
            'redirect_uris': [current_app.config['GOOGLE_REDIRECT_URI']],
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=current_app.config['GOOGLE_REDIRECT_URI'],
    )
    return flow


def _make_unique_username(base: str) -> str:
    """
    Return a username derived from *base* that does not already exist in the
    ``user`` table.  If *base* is taken, appends an incrementing integer
    suffix (e.g. 'jason2', 'jason3', …).
    """
    # Strip non-alphanumeric characters, lower-case, max 40 chars
    cleaned = re.sub(r'[^a-z0-9]', '', base.lower())[:40] or 'user'

    candidate = cleaned
    suffix = 2
    while True:
        row = db_manager.execute_one(
            'SELECT userID FROM `user` WHERE username = %s',
            (candidate,),
        )
        if row is None:
            return candidate
        candidate = f'{cleaned}{suffix}'
        suffix += 1


def _load_user_by_google_id(google_id: str) -> dict | None:
    """Return a user row from the ``user`` table, or None."""
    return db_manager.execute_one(
        'SELECT * FROM `user` WHERE google_id = %s',
        (google_id,),
    )


def _create_user(google_id: str, email: str, name: str) -> dict:
    """
    Insert a new user row with approval_status='pending'.

    Returns the newly-inserted user row fetched by userID.
    """
    new_id = str(uuid.uuid4())
    base   = email.split('@')[0]
    username = _make_unique_username(base)

    db_manager.execute_insert(
        """
        INSERT INTO `user`
            (userID, google_id, email, name, username,
             approval_status, active, admin, created, created_by)
        VALUES
            (%s, %s, %s, %s, %s,
             'pending', 0, 0, NOW(), %s)
        """,
        (new_id, google_id, email, name, username, new_id),
    )
    return db_manager.execute_one(
        'SELECT * FROM `user` WHERE userID = %s',
        (new_id,),
    )


def _load_permissions(user_id: str) -> tuple[int, int]:
    """
    Return (perm_read, perm_write) for *user_id* from the most recent
    ``user_permission`` row, or (0, 0) if no row exists.
    """
    row = db_manager.execute_one(
        """
        SELECT `read`, `write`
        FROM user_permission
        WHERE userID = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,),
    )
    if row is None:
        return 0, 0
    return int(row['read'] or 0), int(row['write'] or 0)


def _load_timezone(user_id: str) -> str:
    row = db_manager.execute_one(
        "SELECT value FROM user_preference WHERE userID = %s AND preference = 'timezone' ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    return (row['value'] or 'UTC') if row else 'UTC'


def _set_session(user: dict) -> None:
    """Populate Flask session from *user* dict and permission table."""
    perm_read, perm_write = _load_permissions(user['userID'])
    session.clear()
    session.permanent     = True
    session['user_id']    = user['userID']
    session['username']   = user['username']
    session['perm_read']  = perm_read
    session['perm_write'] = perm_write
    session['timezone']   = _load_timezone(user['userID'])


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@auth_bp.route('/login')
def login():
    """Render the sign-in page."""
    if session.get('user_id'):
        username = session['username']
        return redirect(url_for('dashboard.index', username=username))
    return render_template('auth.html')


@auth_bp.route('/login/google')
def google_login():
    """Start the Google OAuth 2.0 authorisation flow."""
    flow = _build_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='select_account',
    )
    session['oauth_state'] = state
    return redirect(authorization_url)


@auth_bp.route('/oauth2callback')
def oauth2callback():
    """
    Handle the Google OAuth 2.0 callback.

    Exchanges the authorisation code for tokens, fetches the user's Google
    profile, then finds or creates the local user record before establishing
    a session.
    """
    # Reject if state is missing or mismatched (CSRF protection)
    state = session.get('oauth_state')
    if not state or state != request.args.get('state'):
        flash('Authentication failed: invalid state parameter.', 'error')
        return redirect(url_for('auth.login'))

    # Exchange code for tokens
    flow = _build_flow()
    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as exc:
        current_app.logger.warning('OAuth token exchange failed: %s', exc)
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

    credentials = flow.credentials

    # Verify ID token and extract user info
    try:
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            current_app.config['GOOGLE_CLIENT_ID'],
        )
    except Exception as exc:
        current_app.logger.warning('ID token verification failed: %s', exc)
        flash('Authentication failed: could not verify identity.', 'error')
        return redirect(url_for('auth.login'))

    google_id = id_info.get('sub')
    email     = id_info.get('email', '')
    name      = id_info.get('name', email.split('@')[0])

    if not google_id:
        flash('Authentication failed: missing user identifier.', 'error')
        return redirect(url_for('auth.login'))

    # Find or create user
    user = _load_user_by_google_id(google_id)
    is_new = user is None

    if is_new:
        user = _create_user(google_id, email, name)
        email_service.send_admin_alert(
            subject='New user registration pending approval',
            message=(
                f'A new user has registered and is awaiting approval.\n\n'
                f'Name:     {name}\n'
                f'Email:    {email}\n'
                f'Username: {user["username"]}\n'
                f'UserID:   {user["userID"]}\n'
            ),
        )

    approval = user.get('approval_status', 'pending')

    if approval == 'pending':
        session['pending_username'] = user.get('username', '')
        return redirect(url_for('auth.pending_approval'))

    if approval == 'rejected':
        flash('Your account registration was not approved. Please contact the administrator.', 'error')
        return redirect(url_for('auth.login'))

    # approved
    # Persist tokens so other services (gmail, calendar) can use them
    try:
        db_manager.execute_update(
            """
            UPDATE `user`
            SET access_token = %s,
                refresh_token = %s,
                token_expires = DATE_ADD(NOW(), INTERVAL 3600 SECOND)
            WHERE userID = %s
            """,
            (credentials.token, credentials.refresh_token, user['userID']),
        )
    except Exception as exc:
        current_app.logger.warning('Failed to persist OAuth tokens: %s', exc)

    _set_session(user)
    return redirect(url_for('dashboard.index', username=user['username']))


@auth_bp.route('/logout')
def logout():
    """Clear the session and redirect to the login page."""
    session.clear()
    flash('You have been signed out.', 'message')
    return redirect(url_for('auth.login'))


@auth_bp.route('/pending-approval')
def pending_approval():
    """Inform a new user that their account is awaiting admin review."""
    return render_template('pending_approval.html')
