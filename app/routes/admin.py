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
    insert default permissions (read=32766, write=32766), send approval email.

POST /<username>/admin/users/reject/post/<user_id>
    Reject a pending/approved user: set approval_status='rejected', active=0,
    send rejection email.

POST /<username>/admin/users/permissions/post/<user_id>
    Update perm_read and perm_write for an approved user by inserting a new
    ``user_permission`` row (append-only audit trail).

GET  /<username>/admin/log
    Show the 200 most recent rows from the ``log`` table.

GET  /<username>/admin/topics
    Manage the master topic list (shared tag vocabulary used by study and
    quote to prefill tagging).

GET  /<username>/admin/icon/<image_id>.svg
    Serve a single icon's raw SVG markup (Content-Type: image/svg+xml), for
    use as an image URL elsewhere in the app.

Default permissions on approval
--------------------------------
read  = 32766  (2+4+8+16+32+64+128+256+512+1024+2048+4096+8192+16384 – everything except admin)
write = 32766
"""

import json
import os
import platform
import subprocess
import uuid
from datetime import date, timedelta

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

from app.models.topic_model import TopicModel
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
    PERM_STUDY,
    PERM_QUOTE,
)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

admin_bp = Blueprint('admin', __name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PERM_READ  = 32766   # all non-admin feature bits (bits 1–14)
DEFAULT_PERM_WRITE = 32766

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
    (PERM_STUDY,       'Study'),
    (PERM_QUOTE,       'Quote'),
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


def _get_all_icons() -> list[dict]:
    return db_manager.execute_query(
        'SELECT imageID, name, description, svg FROM svg ORDER BY name'
    )


def _get_icon_by_id(image_id: str) -> dict | None:
    return db_manager.execute_one(
        'SELECT imageID, name, description, svg FROM svg WHERE imageID = %s',
        (image_id,),
    )


def _server_health() -> dict:
    """Return server metrics from /proc on Linux; empty dict with unavailable=True elsewhere."""
    info: dict = {}
    try:
        if platform.system() != 'Linux':
            info['unavailable'] = True
            return info

        with open('/proc/uptime') as f:
            secs = float(f.read().split()[0])
        days, rem = divmod(int(secs), 86400)
        hours, rem = divmod(rem, 3600)
        info['uptime'] = f"{days}d {hours}h {rem // 60}m"

        with open('/proc/loadavg') as f:
            parts = f.read().split()
        info['load'] = f"{parts[0]}, {parts[1]}, {parts[2]}"

        with open('/proc/meminfo') as f:
            mem: dict = {}
            for line in f:
                if ':' in line:
                    k, v = line.split(':', 1)
                    mem[k.strip()] = int(v.split()[0])
        total = mem.get('MemTotal', 1)
        avail = mem.get('MemAvailable', mem.get('MemFree', 0))
        info['mem_pct'] = round((total - avail) / total * 100, 1)

        st = os.statvfs('/')
        disk_total = st.f_blocks * st.f_frsize
        disk_free  = st.f_bfree  * st.f_frsize
        info['disk_pct'] = round((disk_total - disk_free) / disk_total * 100, 1)
    except Exception:
        info['unavailable'] = True
    return info


def _get_dashboard_stats() -> dict:
    """Aggregate stats for the admin dashboard."""
    user_row = db_manager.execute_one(
        "SELECT COUNT(*) as total, SUM(approval_status = 'pending') as pending FROM `user`"
    ) or {}

    req_today = (db_manager.execute_one(
        "SELECT COUNT(*) as n FROM log WHERE DATE(created) = CURDATE()"
    ) or {}).get('n', 0)
    req_week = (db_manager.execute_one(
        "SELECT COUNT(*) as n FROM log WHERE created >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
    ) or {}).get('n', 0)
    req_total = (db_manager.execute_one(
        "SELECT COUNT(*) as n FROM log"
    ) or {}).get('n', 0)

    daily_rows = db_manager.execute_query(
        """
        SELECT DATE(created) as day, COUNT(*) as n
        FROM log
        WHERE created >= DATE_SUB(CURDATE(), INTERVAL 29 DAY)
        GROUP BY DATE(created)
        ORDER BY day
        """
    )
    day_map = {str(r['day']): r['n'] for r in daily_rows}
    today = date.today()
    chart_labels, chart_values = [], []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        chart_labels.append(d.strftime('%b %d'))
        chart_values.append(day_map.get(str(d), 0))

    top_pages = db_manager.execute_query(
        """
        SELECT resource, COUNT(*) as n
        FROM log
        WHERE created >= DATE_SUB(NOW(), INTERVAL 30 DAY)
          AND resource NOT LIKE '/static/%'
        GROUP BY resource
        ORDER BY n DESC
        LIMIT 15
        """
    )

    media_by_kind = db_manager.execute_query(
        """
        SELECT m.kind, COUNT(DISTINCT m.mediaID) as n
        FROM media m
        WHERE m.title IS NOT NULL
          AND m.id = (SELECT MAX(m2.id) FROM media m2 WHERE m2.mediaID = m.mediaID)
        GROUP BY m.kind
        ORDER BY m.kind
        """
    )

    todo_count = (db_manager.execute_one(
        """
        SELECT COUNT(DISTINCT t.todoID) as n
        FROM todo t
        WHERE t.title IS NOT NULL
          AND t.id = (SELECT MAX(t2.id) FROM todo t2 WHERE t2.todoID = t.todoID)
        """
    ) or {}).get('n', 0)

    habit_count = (db_manager.execute_one(
        """
        SELECT COUNT(DISTINCT h.habitID) as n
        FROM habit h
        WHERE h.name IS NOT NULL
          AND h.id = (SELECT MAX(h2.id) FROM habit h2 WHERE h2.habitID = h.habitID)
        """
    ) or {}).get('n', 0)

    return {
        'total_users':   user_row.get('total', 0),
        'pending_users': int(user_row.get('pending') or 0),
        'req_today':     req_today,
        'req_week':      req_week,
        'req_total':     req_total,
        'chart_labels':  json.dumps(chart_labels),
        'chart_values':  json.dumps(chart_values),
        'top_pages':     top_pages,
        'media_by_kind': media_by_kind,
        'todo_count':    todo_count,
        'habit_count':   habit_count,
    }


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


@admin_bp.route('/errors')
@login_required
@permission_required_read(PERM_ADMIN)
def errors(username: str):
    """Render the error log page — journalctl priority err and above."""
    error_log  = None
    error_msg  = None

    if platform.system() != 'Linux':
        error_msg = 'Error logs are only available on the Linux production host (journalctl).'
    else:
        try:
            r = subprocess.run(
                ['journalctl', '-u', 'jttbh', '-p', 'err', '-n', '500', '--no-pager'],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                error_log = r.stdout or None
                if not error_log:
                    error_msg = 'No error-level log entries found.'
            else:
                error_msg = f'journalctl exited {r.returncode}: {r.stderr.strip()}'
        except FileNotFoundError:
            error_msg = 'journalctl not found on this host.'
        except Exception as exc:
            error_msg = f'Could not read error log: {exc}'

    return render_template(
        'admin_errors.html',
        username=username,
        area='admin',
        error_log=error_log,
        error_msg=error_msg,
    )


@admin_bp.route('/dashboard')
@login_required
@permission_required_read(PERM_ADMIN)
def dashboard(username: str):
    """Render the admin dashboard with site and server statistics."""
    return render_template(
        'admin_dashboard.html',
        username=username,
        area='admin',
        stats=_get_dashboard_stats(),
        health=_server_health(),
    )


@admin_bp.route('/log')
@login_required
@permission_required_read(PERM_ADMIN)
def log(username: str):
    """Render the access log with optional filters."""
    q         = request.args.get('q',    '').strip()
    user_f    = request.args.get('user', '').strip()
    from_date = request.args.get('from', '').strip()
    to_date   = request.args.get('to',   '').strip()

    where, params = ['1=1'], []
    if q:
        where.append('resource LIKE %s')
        params.append(f'%{q}%')
    if user_f:
        where.append('username = %s')
        params.append(user_f)
    if from_date:
        where.append('DATE(created) >= %s')
        params.append(from_date)
    if to_date:
        where.append('DATE(created) <= %s')
        params.append(to_date)

    rows = db_manager.execute_query(
        f"""
        SELECT id, userid, username, resource, `get`, `post`, ip, user_agent, created
        FROM log
        WHERE {' AND '.join(where)}
        ORDER BY id DESC
        LIMIT 500
        """,
        tuple(params),
    )

    server_log = None
    error_log  = None
    try:
        r = subprocess.run(
            ['journalctl', '-u', 'jttbh', '-n', '150', '--no-pager'],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            server_log = r.stdout

        r2 = subprocess.run(
            ['journalctl', '-u', 'jttbh', '-p', 'err', '-n', '200', '--no-pager'],
            capture_output=True, text=True, timeout=5,
        )
        if r2.returncode == 0:
            error_log = r2.stdout or None
    except Exception:
        pass

    return render_template(
        'admin_log.html',
        username=username,
        area='admin',
        log_rows=rows,
        server_log=server_log,
        error_log=error_log,
        filters={'q': q, 'user': user_f, 'from': from_date, 'to': to_date},
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


# ---------------------------------------------------------------------------
# Routes – Icons
# ---------------------------------------------------------------------------

@admin_bp.route('/icons')
@login_required
@permission_required_read(PERM_ADMIN)
def icons(username: str):
    """Render the icon management page."""
    return render_template(
        'admin_icons.html',
        username=username,
        area='admin',
        icons=_get_all_icons(),
    )


@admin_bp.route('/icon/<image_id>.svg')
@login_required
@permission_required_read(PERM_ADMIN)
def icon_svg(username: str, image_id: str):
    """Serve a single icon's raw SVG markup, for use as an image URL."""
    icon = _get_icon_by_id(image_id)
    if icon is None:
        abort(404)
    return icon['svg'], 200, {'Content-Type': 'image/svg+xml'}


@admin_bp.route('/icon/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_ADMIN)
@permission_required_write(PERM_ADMIN)
def icon_create(username: str):
    """Insert a new SVG icon."""
    name = request.form.get('name', '').strip()
    svg  = request.form.get('svg',  '').strip()
    if not name or not svg:
        flash('Name and SVG code are required.', 'error')
        return redirect(url_for('admin.icons', username=username))
    description = request.form.get('description', '').strip() or None
    db_manager.execute_insert(
        'INSERT INTO svg (imageID, name, description, svg, created_by) VALUES (%s, %s, %s, %s, %s)',
        (str(uuid.uuid4()), name, description, svg, session['user_id']),
    )
    flash(f'Icon "{name}" added.', 'success')
    return redirect(url_for('admin.icons', username=username))


@admin_bp.route('/icon/update/post/<image_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_ADMIN)
@permission_required_write(PERM_ADMIN)
def icon_update(username: str, image_id: str):
    """Update an existing SVG icon."""
    if _get_icon_by_id(image_id) is None:
        abort(404)
    name = request.form.get('name', '').strip()
    svg  = request.form.get('svg',  '').strip()
    if not name or not svg:
        flash('Name and SVG code are required.', 'error')
        return redirect(url_for('admin.icons', username=username))
    description = request.form.get('description', '').strip() or None
    db_manager.execute_update(
        'UPDATE svg SET name=%s, description=%s, svg=%s WHERE imageID=%s',
        (name, description, svg, image_id),
    )
    flash(f'Icon "{name}" updated.', 'success')
    return redirect(url_for('admin.icons', username=username))


@admin_bp.route('/icon/delete/post/<image_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_ADMIN)
@permission_required_write(PERM_ADMIN)
def icon_delete(username: str, image_id: str):
    """Hard-delete an SVG icon."""
    icon = _get_icon_by_id(image_id)
    if icon is None:
        abort(404)
    db_manager.execute_update('DELETE FROM svg WHERE imageID=%s', (image_id,))
    flash(f'Icon "{icon["name"]}" deleted.', 'success')
    return redirect(url_for('admin.icons', username=username))


# ---------------------------------------------------------------------------
# Routes – Topics (master tag list, shared across features)
# ---------------------------------------------------------------------------

@admin_bp.route('/topics')
@login_required
@permission_required_read(PERM_ADMIN)
def topics(username: str):
    """Render the topic management page."""
    return render_template(
        'admin_topics.html',
        username=username,
        area='admin',
        topics=TopicModel.get_all(),
    )


@admin_bp.route('/topic/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_ADMIN)
@permission_required_write(PERM_ADMIN)
def topic_create(username: str):
    """Add a new topic."""
    name = request.form.get('name', '').strip()
    if not name:
        flash('Topic name is required.', 'error')
        return redirect(url_for('admin.topics', username=username))
    if TopicModel.create(name, session['user_id']) is None:
        flash(f'Topic "{name}" already exists.', 'warning')
    else:
        flash(f'Topic "{name}" added.', 'success')
    return redirect(url_for('admin.topics', username=username))


@admin_bp.route('/topic/delete/post/<int:topic_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_ADMIN)
@permission_required_write(PERM_ADMIN)
def topic_delete(username: str, topic_id: int):
    """Delete a topic."""
    TopicModel.delete(topic_id)
    flash('Topic deleted.', 'success')
    return redirect(url_for('admin.topics', username=username))
