"""
JTTBH Admin Routes
====================
Routes for the administrator area.  Only users with PERM_ADMIN may access
any of these endpoints.

Routes
------
GET  /<username>/admin/users
    List all users grouped by approval status (pending first).

POST /<username>/admin/users/approve/post/<user_id>
    Approve a pending user: set approval_status='approved', active=1,
    insert default permissions (read=8190, write=8190), send approval email.

POST /<username>/admin/users/reject/post/<user_id>
    Reject a pending/approved user: set approval_status='rejected', active=0,
    send rejection email.

POST /<username>/admin/users/permissions/post/<user_id>
    Update perm_read and perm_write for an approved user by inserting a new
    ``user_permission`` row (append-only audit trail).

GET  /<username>/admin/log
    Show the 200 most recent rows from the ``log`` table.

Default permissions on approval
--------------------------------
read  = 8190   (2+4+8+16+32+64+128+256+512+1024+2048+4096 – everything except admin)
write = 8190
"""

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    abort,
)

from app.services.database import db_manager
from app.services.email_service import email_service
from app.services.decorators import (
    login_required,
    permission_required_read,
    permission_required_write,
    PERM_ADMIN,
    PERM_PODCAST,
    PERM_APPOINTMENT,
    PERM_DASHBOARD,
    PERM_TODO,
    PERM_HABIT,
    PERM_PROJECT,
    PERM_TRIAGE,
    PERM_BOOKMARK,
    PERM_FITNESS,
    PERM_CHORE,
    PERM_BOOK,
    PERM_JOURNAL,
)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

admin_bp = Blueprint('admin', __name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PERM_READ  = 8190   # all non-admin feature bits
DEFAULT_PERM_WRITE = 8190

# Ordered list of (bit, label) for the permissions checkbox matrix
PERM_LABELS = [
    (PERM_ADMIN,       'Admin'),
    (PERM_PODCAST,     'Podcast'),
    (PERM_APPOINTMENT, 'Appointment'),
    (PERM_DASHBOARD,   'Dashboard'),
    (PERM_TODO,        'Todo'),
    (PERM_HABIT,       'Habit'),
    (PERM_PROJECT,     'Project'),
    (PERM_TRIAGE,      'Triage'),
    (PERM_BOOKMARK,    'Bookmark'),
    (PERM_FITNESS,     'Fitness'),
    (PERM_CHORE,       'Chore'),
    (PERM_BOOK,        'Book'),
    (PERM_JOURNAL,     'Journal'),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_all_users() -> list[dict]:
    """Return all user rows, pending ones first, then alphabetically."""
    return db_manager.execute_query(
        """
        SELECT
            u.userID,
            u.username,
            u.email,
            u.name,
            u.approval_status,
            u.active,
            u.admin,
            u.created,
            p.`read`  AS perm_read,
            p.`write` AS perm_write
        FROM `user` u
        LEFT JOIN user_permission p
            ON p.userID = u.userID
            AND p.id = (
                SELECT MAX(p2.id)
                FROM user_permission p2
                WHERE p2.userID = u.userID
            )
        ORDER BY
            FIELD(u.approval_status, 'pending', 'approved', 'rejected'),
            u.name
        """,
    )


def _get_user_by_id(user_id: str) -> dict | None:
    """Return a single user row by primary key."""
    return db_manager.execute_one(
        'SELECT * FROM `user` WHERE userID = %s',
        (user_id,),
    )


# ---------------------------------------------------------------------------
# Routes – GET
# ---------------------------------------------------------------------------

@admin_bp.route('/users')
@login_required
@permission_required_read(PERM_ADMIN)
def users(username: str):
    """Render the user management page."""
    all_users = _get_all_users()
    return render_template(
        'admin_users.html',
        username=username,
        area='admin',
        users=all_users,
        perm_labels=PERM_LABELS,
    )


@admin_bp.route('/log')
@login_required
@permission_required_read(PERM_ADMIN)
def log(username: str):
    """Render the recent access-log page."""
    rows = db_manager.execute_query(
        """
        SELECT
            l.id,
            l.user_id,
            u.username,
            l.method,
            l.path,
            l.status_code,
            l.ip_address,
            l.created_at
        FROM log l
        LEFT JOIN `user` u ON u.userID = l.user_id
        ORDER BY l.id DESC
        LIMIT 200
        """,
    )
    return render_template(
        'admin_log.html',
        username=username,
        area='admin',
        log_rows=rows,
    )


# ---------------------------------------------------------------------------
# Routes – POST (PRG pattern)
# ---------------------------------------------------------------------------

@admin_bp.route('/users/approve/post/<user_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_ADMIN)
@permission_required_write(PERM_ADMIN)
def approve_user(username: str, user_id: str):
    """
    Approve a pending user.

    1. Set approval_status='approved', active=1.
    2. Insert a user_permission row with default read/write bits.
    3. Send approval notification email.
    4. PRG redirect to the users list.
    """
    target = _get_user_by_id(user_id)
    if target is None:
        abort(404)

    acting_user_id = session['user_id']

    db_manager.execute_update(
        """
        UPDATE `user`
        SET approval_status = 'approved',
            active = 1
        WHERE userID = %s
        """,
        (user_id,),
    )

    # Only insert permissions if none exist yet (avoid stacking)
    existing = db_manager.execute_one(
        'SELECT id FROM user_permission WHERE userID = %s ORDER BY id DESC LIMIT 1',
        (user_id,),
    )
    if existing is None:
        db_manager.execute_insert(
            """
            INSERT INTO user_permission (userID, `read`, `write`, created, created_by)
            VALUES (%s, %s, %s, NOW(), %s)
            """,
            (user_id, DEFAULT_PERM_READ, DEFAULT_PERM_WRITE, acting_user_id),
        )

    email_service.send_approval_notification(
        user_email=target['email'],
        username=target['username'],
        approved=True,
    )

    flash(f'User {target["username"]} has been approved.', 'success')
    return redirect(url_for('admin.users', username=username))


@admin_bp.route('/users/reject/post/<user_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_ADMIN)
@permission_required_write(PERM_ADMIN)
def reject_user(username: str, user_id: str):
    """
    Reject a user's registration.

    1. Set approval_status='rejected', active=0.
    2. Send rejection notification email.
    3. PRG redirect to the users list.
    """
    target = _get_user_by_id(user_id)
    if target is None:
        abort(404)

    db_manager.execute_update(
        """
        UPDATE `user`
        SET approval_status = 'rejected',
            active = 0
        WHERE userID = %s
        """,
        (user_id,),
    )

    email_service.send_approval_notification(
        user_email=target['email'],
        username=target['username'],
        approved=False,
    )

    flash(f'User {target["username"]} has been rejected.', 'message')
    return redirect(url_for('admin.users', username=username))


@admin_bp.route('/users/permissions/post/<user_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_ADMIN)
@permission_required_write(PERM_ADMIN)
def update_permissions(username: str, user_id: str):
    """
    Update permission bits for a user by inserting a new user_permission row.

    Form data
    ---------
    perm_read  – integer value of the read bitmask (sum of checked boxes)
    perm_write – integer value of the write bitmask (sum of checked boxes)
    """
    target = _get_user_by_id(user_id)
    if target is None:
        abort(404)

    try:
        perm_read  = int(request.form.get('perm_read',  0))
        perm_write = int(request.form.get('perm_write', 0))
    except (ValueError, TypeError):
        flash('Invalid permission values.', 'error')
        return redirect(url_for('admin.users', username=username))

    acting_user_id = session['user_id']

    db_manager.execute_insert(
        """
        INSERT INTO user_permission (userID, `read`, `write`, created, created_by)
        VALUES (%s, %s, %s, NOW(), %s)
        """,
        (user_id, perm_read, perm_write, acting_user_id),
    )

    flash(f'Permissions updated for {target["username"]}.', 'success')
    return redirect(url_for('admin.users', username=username))
