"""
Project Model
=============
Data-access layer for the agent-collaboration parts of the Projects feature:
the checkable plan (``project_task``), the two-way thread (``project_message``),
project ``status`` / ``parentID``, and the propose -> approve subproject flow.

Existing project CRUD stays inline in ``app/routes/project.py``; this model holds
only the concerns shared by the web UI and the ``/api/v1`` blueprint.

Patterns
--------
* ``project`` and ``project_task`` are insert-only: update = INSERT a new row
  with the same UUID; soft-delete = INSERT a row with the sentinel column NULL
  (``project.name`` / ``project_task.title``). Current state = row with MAX(id).
* ``project_message`` is append-only. Rows are immutable except ``resolution``,
  which is set once via a direct UPDATE when a proposal is approved/dismissed.
"""

import json
import uuid
from datetime import date, datetime

from app.services.database import db_manager

VALID_STATUS = ('active', 'blocked', 'awaiting_review', 'done')
AGENT_KINDS = ('question', 'progress', 'proposal')


# ---------------------------------------------------------------------------
# SQL fragments
# ---------------------------------------------------------------------------

# A question is "open" when no guidance message was posted after it.
_OPEN_QUESTIONS = """
    (SELECT COUNT(*) FROM project_message q
     WHERE q.projectID = p.projectID
       AND q.author = 'agent' AND q.kind = 'question'
       AND q.id > COALESCE(
           (SELECT MAX(g.id) FROM project_message g
            WHERE g.projectID = p.projectID AND g.kind = 'guidance'), 0))
"""

_CURRENT_PROJECT = f"""
    SELECT p.projectID, p.parentID, p.name, p.description, p.next_step,
           COALESCE(p.status, 'active') AS status, p.position,
           {_OPEN_QUESTIONS} AS open_questions
    FROM project p
    WHERE p.userID = %s
      AND p.id = (SELECT MAX(p2.id) FROM project p2 WHERE p2.projectID = p.projectID)
      AND p.name IS NOT NULL
"""


class ProjectModel:
    """Shared data access for project status, plan tasks, and the thread."""

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    @staticmethod
    def list_projects(user_id: str) -> list[dict]:
        """All active projects for *user_id*, blocked ones first, then position."""
        return db_manager.execute_query(
            _CURRENT_PROJECT + """
              ORDER BY (COALESCE(p.status, 'active') = 'blocked') DESC, p.position
            """,
            (user_id,),
        )

    @staticmethod
    def get_project(user_id: str, project_id: str) -> dict | None:
        """Current state of one project, or None if not found / not owned."""
        return db_manager.execute_one(
            _CURRENT_PROJECT + " AND p.projectID = %s",
            (user_id, project_id),
        )

    @staticmethod
    def get_detail(user_id: str, project_id: str) -> dict | None:
        """Project row plus its resources, plan tasks, and full message thread."""
        project = ProjectModel.get_project(user_id, project_id)
        if project is None:
            return None
        project['resources'] = db_manager.execute_query(
            """
            SELECT r.resourceID, r.name, r.resource, r.note, r.position
            FROM project_resource r
            WHERE r.projectID = %s
              AND r.id = (SELECT MAX(r2.id) FROM project_resource r2
                          WHERE r2.resourceID = r.resourceID)
              AND r.name IS NOT NULL
            ORDER BY r.position
            """,
            (project_id,),
        )
        project['tasks'] = ProjectModel.list_tasks(project_id)
        project['messages'] = ProjectModel.list_messages(project_id)
        return project

    @staticmethod
    def set_status(user_id: str, project_id: str, *, status: str | None = None,
                   next_step: str | None = None, by: str | None = None) -> bool:
        """Insert a new project row updating status and/or next_step. Returns
        False if the project is missing or *status* is invalid."""
        if status is not None and status not in VALID_STATUS:
            return False
        current = ProjectModel.get_project(user_id, project_id)
        if current is None:
            return False
        ProjectModel._insert_project_row(
            project_id, user_id,
            parent_id=current['parentID'],
            name=current['name'],
            description=current['description'],
            next_step=next_step if next_step is not None else current['next_step'],
            status=status if status is not None else current['status'],
            position=current['position'],
            by=by or user_id,
        )
        return True

    @staticmethod
    def _insert_project_row(project_id, user_id, *, parent_id, name, description,
                            next_step, status, position, by):
        db_manager.execute_insert(
            """
            INSERT INTO project
                (projectID, userID, parentID, name, description, next_step,
                 status, position, created, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (project_id, user_id, parent_id, name, description or None,
             next_step or None, status or None, position, datetime.now(), by),
        )

    # ------------------------------------------------------------------
    # Plan tasks (agent writes, Jason reads)
    # ------------------------------------------------------------------

    @staticmethod
    def list_tasks(project_id: str) -> list[dict]:
        return db_manager.execute_query(
            """
            SELECT t.taskID, t.title, t.done, t.position, t.note
            FROM project_task t
            WHERE t.projectID = %s
              AND t.id = (SELECT MAX(t2.id) FROM project_task t2
                          WHERE t2.taskID = t.taskID)
              AND t.title IS NOT NULL
            ORDER BY t.position, t.id
            """,
            (project_id,),
        )

    @staticmethod
    def _get_task(project_id: str, task_id: str) -> dict | None:
        return db_manager.execute_one(
            """
            SELECT t.taskID, t.title, t.done, t.position, t.note
            FROM project_task t
            WHERE t.projectID = %s AND t.taskID = %s
              AND t.id = (SELECT MAX(t2.id) FROM project_task t2
                          WHERE t2.taskID = t.taskID)
              AND t.title IS NOT NULL
            """,
            (project_id, task_id),
        )

    @staticmethod
    def add_task(project_id: str, title: str, *, note: str | None = None,
                 position: int | None = None, by: str | None = None) -> str:
        if position is None:
            row = db_manager.execute_one(
                """
                SELECT MAX(t.position) AS m FROM project_task t
                WHERE t.projectID = %s
                  AND t.id = (SELECT MAX(t2.id) FROM project_task t2
                              WHERE t2.taskID = t.taskID)
                  AND t.title IS NOT NULL
                """,
                (project_id,),
            )
            position = (row['m'] + 1) if row and row['m'] is not None else 0
        task_id = str(uuid.uuid4())
        ProjectModel._insert_task_row(task_id, project_id, title, 0, position, note, by)
        return task_id

    @staticmethod
    def update_task(project_id: str, task_id: str, *, title=None, done=None,
                    note=None, position=None, by: str | None = None) -> bool:
        current = ProjectModel._get_task(project_id, task_id)
        if current is None:
            return False
        ProjectModel._insert_task_row(
            task_id, project_id,
            title if title is not None else current['title'],
            int(bool(done)) if done is not None else current['done'],
            position if position is not None else current['position'],
            note if note is not None else current['note'],
            by,
        )
        return True

    @staticmethod
    def delete_task(project_id: str, task_id: str, by: str | None = None) -> bool:
        current = ProjectModel._get_task(project_id, task_id)
        if current is None:
            return False
        ProjectModel._insert_task_row(
            task_id, project_id, None, current['done'], current['position'],
            current['note'], by,
        )
        return True

    @staticmethod
    def _insert_task_row(task_id, project_id, title, done, position, note, by):
        db_manager.execute_insert(
            """
            INSERT INTO project_task
                (taskID, projectID, title, done, position, note, created, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (task_id, project_id, title, done, position, note or None,
             datetime.now(), by),
        )

    # ------------------------------------------------------------------
    # Message thread
    # ------------------------------------------------------------------

    @staticmethod
    def list_messages(project_id: str, since_id: int = 0) -> list[dict]:
        """Messages with id > *since_id*, oldest first (agent poll cursor)."""
        rows = db_manager.execute_query(
            """
            SELECT m.id, m.messageID, m.author, m.kind, m.body, m.meta,
                   m.resolution, m.created
            FROM project_message m
            WHERE m.projectID = %s AND m.id > %s
            ORDER BY m.id
            """,
            (project_id, since_id),
        )
        for r in rows:
            if isinstance(r.get('created'), (date, datetime)):
                r['created'] = r['created'].isoformat()
            if r.get('meta'):
                try:
                    r['meta'] = json.loads(r['meta'])
                except (ValueError, TypeError):
                    pass
        return rows

    @staticmethod
    def add_message(project_id: str, author: str, kind: str, body: str, *,
                    meta: dict | None = None, by: str | None = None,
                    user_id: str | None = None) -> str:
        """Append a message. An agent question also flips the project to
        ``blocked`` (needs Jason); guidance from Jason flips it back to
        ``active`` if it was blocked."""
        message_id = str(uuid.uuid4())
        db_manager.execute_insert(
            """
            INSERT INTO project_message
                (messageID, projectID, author, kind, body, meta, created, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (message_id, project_id, author, kind, body or None,
             json.dumps(meta) if meta else None, datetime.now(), by),
        )

        owner = user_id or ProjectModel._owner_of(project_id)
        if owner:
            if author == 'agent' and kind == 'question':
                ProjectModel._transition(owner, project_id, to='blocked', by=by)
            elif author == 'user' and kind == 'guidance':
                ProjectModel._transition(owner, project_id, to='active',
                                         only_if='blocked', by=by)
        return message_id

    @staticmethod
    def _transition(user_id, project_id, *, to, only_if=None, by=None):
        current = ProjectModel.get_project(user_id, project_id)
        if current is None:
            return
        if only_if is not None and current['status'] != only_if:
            return
        if current['status'] == to:
            return
        ProjectModel.set_status(user_id, project_id, status=to, by=by or user_id)

    @staticmethod
    def _owner_of(project_id: str) -> str | None:
        row = db_manager.execute_one(
            "SELECT userID FROM project WHERE projectID = %s LIMIT 1",
            (project_id,),
        )
        return row['userID'] if row else None

    # ------------------------------------------------------------------
    # Propose -> approve subprojects
    # ------------------------------------------------------------------

    @staticmethod
    def resolve_proposal(user_id: str, message_id: str, action: str) -> dict | None:
        """Approve or dismiss a proposal message.

        ``approve`` creates a child project (parentID = the thread's project) and
        marks the message ``resolution='approved'``; returns
        ``{'child_id': <projectID>}``. ``dismiss`` sets
        ``resolution='dismissed'`` and returns ``{}``. Returns None if the
        message is missing, not a pending proposal, or not owned by *user_id*.
        """
        msg = db_manager.execute_one(
            """
            SELECT m.messageID, m.projectID, m.kind, m.body, m.meta, m.resolution
            FROM project_message m
            JOIN project p ON p.projectID = m.projectID
            WHERE m.messageID = %s AND p.userID = %s
            LIMIT 1
            """,
            (message_id, user_id),
        )
        if not msg or msg['kind'] != 'proposal' or msg['resolution'] is not None:
            return None

        parent_id = msg['projectID']

        if action == 'dismiss':
            db_manager.execute_update(
                "UPDATE project_message SET resolution = 'dismissed' WHERE messageID = %s",
                (message_id,),
            )
            return {'parent_id': parent_id}

        if action != 'approve':
            return None

        meta = {}
        if msg['meta']:
            try:
                meta = json.loads(msg['meta'])
            except (ValueError, TypeError):
                meta = {}
        title = (meta.get('title') or 'Untitled subproject')[:255]
        description = meta.get('description') or msg['body']

        pos_row = db_manager.execute_one(
            """
            SELECT MAX(p.position) AS m FROM project p
            WHERE p.userID = %s
              AND p.id = (SELECT MAX(p2.id) FROM project p2 WHERE p2.projectID = p.projectID)
              AND p.name IS NOT NULL
            """,
            (user_id,),
        )
        position = (pos_row['m'] + 1) if pos_row and pos_row['m'] is not None else 0

        child_id = str(uuid.uuid4())
        ProjectModel._insert_project_row(
            child_id, user_id, parent_id=parent_id, name=title,
            description=description, next_step=None, status='active',
            position=position, by=user_id,
        )
        db_manager.execute_update(
            "UPDATE project_message SET resolution = 'approved' WHERE messageID = %s",
            (message_id,),
        )
        return {'child_id': child_id, 'parent_id': parent_id}
