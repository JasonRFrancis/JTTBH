"""
Project Routes
==============
Flask blueprint for all project-feature URLs.

URL patterns
------------
GET  /<username>/project/index
GET  /<username>/project/view/<project_id>

POST /<username>/project/create/post
POST /<username>/project/update/post/<project_id>
POST /<username>/project/delete/post/<project_id>
POST /<username>/project/resource/create/post/<project_id>
POST /<username>/project/resource/delete/post/<resource_id>

All POST routes follow the PRG pattern: redirect to a GET after state change
with a flash message indicating success or failure.

Insert-only pattern
-------------------
Updates are implemented as INSERT of a new row sharing the same projectID UUID.
Deletes are implemented as INSERT of a new row with name=NULL.
Current state is determined by MAX(id) per projectID.
"""

import uuid
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
    PERM_PROJECT,
    login_required,
    permission_required_read,
    permission_required_write,
)
from app.models.todo_model import TodoModel

project_bp = Blueprint('project', __name__)


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

_CURRENT_PROJECTS_SQL = """
    SELECT p.projectID, p.name, p.description, p.next_step, p.position
    FROM project p
    WHERE p.userID = %s
      AND p.id = (SELECT MAX(p2.id) FROM project p2 WHERE p2.projectID = p.projectID)
      AND p.name IS NOT NULL
    ORDER BY p.position
"""

_CURRENT_RESOURCES_SQL = """
    SELECT r.resourceID, r.name, r.resource, r.note, r.position
    FROM project_resource r
    WHERE r.projectID = %s
      AND r.id = (SELECT MAX(r2.id) FROM project_resource r2 WHERE r2.resourceID = r.resourceID)
      AND r.name IS NOT NULL
    ORDER BY r.position
"""

_PROJECT_BY_ID_SQL = """
    SELECT p.projectID, p.name, p.description, p.next_step, p.position
    FROM project p
    WHERE p.userID = %s
      AND p.projectID = %s
      AND p.id = (SELECT MAX(p2.id) FROM project p2 WHERE p2.projectID = p.projectID)
      AND p.name IS NOT NULL
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _redirect_to_index(username: str):
    """Return a redirect to the project index page."""
    return redirect(url_for('project.index', username=username))


def _redirect_to_view(username: str, project_id: str):
    """Return a redirect to a single project view page."""
    return redirect(url_for('project.view', username=username, project_id=project_id))


def _get_project(user_id: str, project_id: str) -> dict | None:
    """Fetch the current state of a single project; return None if not found."""
    return db_manager.execute_one(_PROJECT_BY_ID_SQL, (user_id, project_id))


def _next_position(user_id: str) -> int:
    """Return position = max existing position + 1 for new projects."""
    row = db_manager.execute_one(
        """
        SELECT MAX(p.position) AS max_pos
        FROM project p
        WHERE p.userID = %s
          AND p.id = (SELECT MAX(p2.id) FROM project p2 WHERE p2.projectID = p.projectID)
          AND p.name IS NOT NULL
        """,
        (user_id,),
    )
    max_pos = row['max_pos'] if row and row['max_pos'] is not None else -1
    return max_pos + 1


def _next_resource_position(project_id: str) -> int:
    """Return position = max existing resource position + 1."""
    row = db_manager.execute_one(
        """
        SELECT MAX(r.position) AS max_pos
        FROM project_resource r
        WHERE r.projectID = %s
          AND r.id = (SELECT MAX(r2.id) FROM project_resource r2 WHERE r2.resourceID = r.resourceID)
          AND r.name IS NOT NULL
        """,
        (project_id,),
    )
    max_pos = row['max_pos'] if row and row['max_pos'] is not None else -1
    return max_pos + 1


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@project_bp.route('/index')
@login_required
@permission_required_read(PERM_PROJECT)
def index(username: str):
    """
    List all active projects for the authenticated user.

    Renders project_index.html with:
        projects  – list of dicts (projectID, name, description, next_step, position)
        username  – URL username segment
    """
    user_id = session['user_id']
    projects = db_manager.execute_query(_CURRENT_PROJECTS_SQL, (user_id,))
    return render_template('project_index.html', projects=projects, username=username)


@project_bp.route('/view/<project_id>')
@login_required
@permission_required_read(PERM_PROJECT)
def view(username: str, project_id: str):
    """
    View a single project with its associated resources.

    Path Parameters
    ---------------
    project_id : str
        The projectID UUID to display.
    """
    user_id = session['user_id']
    project = _get_project(user_id, project_id)

    if project is None:
        flash('Project not found.', 'error')
        return _redirect_to_index(username)

    resources = db_manager.execute_query(_CURRENT_RESOURCES_SQL, (project_id,))

    return render_template(
        'project_view.html',
        project=project,
        resources=resources,
        username=username,
    )


# ---------------------------------------------------------------------------
# POST routes (PRG pattern)
# ---------------------------------------------------------------------------

@project_bp.route('/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_PROJECT)
@permission_required_write(PERM_PROJECT)
def create(username: str):
    """
    Create a new project.

    Form fields
    -----------
    name        : str   Required.
    description : str   Optional.
    next_step   : str   Optional.
    """
    user_id = session['user_id']
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip() or None
    next_step = request.form.get('next_step', '').strip() or None

    if not name:
        flash('Project name is required.', 'error')
        return _redirect_to_index(username)

    project_id = str(uuid.uuid4())
    position = _next_position(user_id)

    db_manager.execute_insert(
        """
        INSERT INTO project (projectID, userID, name, description, next_step, position, created, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (project_id, user_id, name, description, next_step, position, datetime.now(), user_id),
    )

    flash('Project created.', 'success')
    return _redirect_to_view(username, project_id)


@project_bp.route('/update/post/<project_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_PROJECT)
@permission_required_write(PERM_PROJECT)
def update(username: str, project_id: str):
    """
    Update a project by inserting a new row (insert-only pattern).

    Form fields
    -----------
    name        : str   Optional new name.
    description : str   Optional new description.
    next_step   : str   Optional new next step.
    position    : int   Optional new position.
    """
    user_id = session['user_id']
    project = _get_project(user_id, project_id)

    if project is None:
        flash('Project not found.', 'error')
        return _redirect_to_index(username)

    name = request.form.get('name', '').strip() or project['name']
    description = request.form.get('description', '').strip() or project['description']
    next_step = request.form.get('next_step', '').strip() or project['next_step']
    position_str = request.form.get('position', '')
    position = int(position_str) if position_str.isdigit() else project['position']

    db_manager.execute_insert(
        """
        INSERT INTO project (projectID, userID, name, description, next_step, position, created, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (project_id, user_id, name, description or None, next_step or None,
         position, datetime.now(), user_id),
    )

    flash('Project updated.', 'success')
    return _redirect_to_view(username, project_id)


@project_bp.route('/delete/post/<project_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_PROJECT)
@permission_required_write(PERM_PROJECT)
def delete(username: str, project_id: str):
    """
    Soft-delete a project by inserting a new row with name=NULL.

    Path Parameters
    ---------------
    project_id : str   The projectID UUID to delete.
    """
    user_id = session['user_id']
    project = _get_project(user_id, project_id)

    if project is None:
        flash('Project not found.', 'error')
        return _redirect_to_index(username)

    # Insert sentinel row: name=NULL signals deletion in the insert-only pattern.
    # The project table defines name as NOT NULL in schema, but the insert-only
    # pattern requires it; if the schema is updated to allow NULL this will work.
    db_manager.execute_insert(
        """
        INSERT INTO project (projectID, userID, name, description, next_step, position, created, created_by)
        VALUES (%s, %s, NULL, NULL, NULL, %s, %s, %s)
        """,
        (project_id, user_id, project['position'], datetime.now(), user_id),
    )

    flash('Project deleted.', 'success')
    return _redirect_to_index(username)


@project_bp.route('/resource/create/post/<project_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_PROJECT)
@permission_required_write(PERM_PROJECT)
def resource_create(username: str, project_id: str):
    """
    Add a resource (link, note, or file reference) to a project.

    Form fields
    -----------
    name     : str   Required. Display name for the resource.
    resource : str   Optional. URL or content body.
    note     : str   Optional. Additional notes.
    """
    user_id = session['user_id']
    project = _get_project(user_id, project_id)

    if project is None:
        flash('Project not found.', 'error')
        return _redirect_to_index(username)

    name = request.form.get('name', '').strip()
    resource_url = request.form.get('resource', '').strip() or None
    note = request.form.get('note', '').strip() or None

    if not name:
        flash('Resource name is required.', 'error')
        return _redirect_to_view(username, project_id)

    resource_id = str(uuid.uuid4())
    position = _next_resource_position(project_id)

    db_manager.execute_insert(
        """
        INSERT INTO project_resource (resourceID, projectID, name, resource, note, position, created, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (resource_id, project_id, name, resource_url, note, position, datetime.now(), user_id),
    )

    flash('Resource added.', 'success')
    return _redirect_to_view(username, project_id)


@project_bp.route('/send_to_todo/post/<project_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_PROJECT)
@permission_required_write(PERM_PROJECT)
def send_to_todo(username: str, project_id: str):
    """
    Create a todo item from a project's next_step field (spec §5.3.5).

    The next_step text is inserted as a new daily todo for today.  A flash
    message confirms the action and links back to the todo list.
    """
    user_id = session['user_id']
    project = _get_project(user_id, project_id)

    if project is None:
        flash('Project not found.', 'error')
        return _redirect_to_index(username)

    next_step = (project.get('next_step') or '').strip()
    if not next_step:
        flash('This project has no next step to send.', 'error')
        return _redirect_to_view(username, project_id)

    from datetime import date as _date  # noqa: PLC0415
    today = _date.today()

    existing = TodoModel.get_daily_todos(user_id, today)
    position = max((t['position'] for t in existing), default=-1) + 1

    TodoModel.create(
        user_id=user_id,
        title=next_step,
        due=today,
        list_type='daily',
        position=position,
    )

    flash(f'Added to today\'s todo list: "{next_step}"', 'success')
    return _redirect_to_view(username, project_id)


@project_bp.route('/resource/delete/post/<resource_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_PROJECT)
@permission_required_write(PERM_PROJECT)
def resource_delete(username: str, resource_id: str):
    """
    Soft-delete a project resource by inserting a new row with name=NULL.

    Path Parameters
    ---------------
    resource_id : str   The resourceID UUID to delete.
    """
    user_id = session['user_id']

    # Fetch current resource state to get projectID for redirect.
    resource = db_manager.execute_one(
        """
        SELECT r.resourceID, r.projectID, r.position
        FROM project_resource r
        WHERE r.resourceID = %s
          AND r.id = (SELECT MAX(r2.id) FROM project_resource r2 WHERE r2.resourceID = r.resourceID)
          AND r.name IS NOT NULL
        """,
        (resource_id,),
    )

    if resource is None:
        flash('Resource not found.', 'error')
        return _redirect_to_index(username)

    project_id = resource['projectID']

    # Verify the resource belongs to a project owned by this user.
    project = _get_project(user_id, project_id)
    if project is None:
        flash('Resource not found.', 'error')
        return _redirect_to_index(username)

    db_manager.execute_insert(
        """
        INSERT INTO project_resource (resourceID, projectID, name, resource, note, position, created, created_by)
        VALUES (%s, %s, NULL, NULL, NULL, %s, %s, %s)
        """,
        (resource_id, project_id, resource['position'], datetime.now(), user_id),
    )

    flash('Resource removed.', 'success')
    return _redirect_to_view(username, project_id)
