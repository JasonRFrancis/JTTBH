"""
Unit Tests: ProjectModel (agent collaboration surface)
=====================================================
Tests encode *why* the behaviour matters:

* An agent question must make the project visibly "blocked" so it surfaces at the
  top of Jason's Projects page — otherwise he never learns the agent is stuck.
* Jason's guidance must automatically unblock the project.
* A progress update must NOT change status (it's routine, not a stop).
* The plan checklist is insert-only: the latest row per taskID wins.
* Approving a proposal must create a real child project linked to its parent and
  mark the proposal resolved so it stops nagging.

All DB access is mocked; no live database.

Run: pytest test/test_project_agent.py -v
"""

import json
import pytest
from unittest.mock import MagicMock

from app.models.project_model import ProjectModel


PROJECT_ID = 'proj-1'
USER_ID = 'user-1'


def _project_row(status='active'):
    return {
        'projectID': PROJECT_ID, 'parentID': None, 'name': 'Test project',
        'description': None, 'next_step': None, 'status': status,
        'position': 0, 'open_questions': 0,
    }


@pytest.fixture
def db(monkeypatch):
    """Route db_manager calls by inspecting the SQL string."""
    mock = MagicMock()

    def execute_one(sql, params=None):
        if 'SELECT userID FROM project' in sql:
            return {'userID': USER_ID}
        if 'MAX(t.position)' in sql or 'MAX(p.position)' in sql:
            return {'m': None}
        if 'FROM project_message m' in sql and 'JOIN project p' in sql:
            return db.proposal_row
        if 'FROM project_task' in sql:         # _get_task
            return db.task_state
        if 'FROM project p' in sql:            # get_project / _CURRENT_PROJECT
            return dict(db.project_state)
        return None

    mock.execute_one.side_effect = execute_one
    mock.execute_query.side_effect = lambda sql, params=None: []
    mock.execute_insert.side_effect = lambda sql, params=None: 1
    mock.execute_update.side_effect = lambda sql, params=None: 1

    monkeypatch.setattr('app.models.project_model.db_manager', mock)
    db.mock = mock
    db.project_state = _project_row()
    db.task_state = None
    db.proposal_row = None
    return db


# ---------------------------------------------------------------------------
# Status transitions driven by the thread
# ---------------------------------------------------------------------------

def test_agent_question_blocks_project(db):
    db.project_state = _project_row(status='active')
    ProjectModel.add_message(PROJECT_ID, 'agent', 'question', 'Which API?',
                             user_id=USER_ID)

    project_inserts = [
        c.args for c in db.mock.execute_insert.call_args_list
        if 'INSERT INTO project\n' in c.args[0]
    ]
    assert project_inserts, 'expected a new project row to record the blocked status'
    assert 'blocked' in project_inserts[-1][1]


def test_progress_update_does_not_change_status(db):
    db.project_state = _project_row(status='active')
    ProjectModel.add_message(PROJECT_ID, 'agent', 'progress', 'Halfway done',
                             user_id=USER_ID)

    assert not [
        c for c in db.mock.execute_insert.call_args_list
        if 'INSERT INTO project\n' in c.args[0]
    ], 'a progress update must not write a status change'


def test_user_guidance_unblocks(db):
    db.project_state = _project_row(status='blocked')
    ProjectModel.add_message(PROJECT_ID, 'user', 'guidance', 'Use API v2',
                             user_id=USER_ID)

    project_inserts = [
        c.args for c in db.mock.execute_insert.call_args_list
        if 'INSERT INTO project\n' in c.args[0]
    ]
    assert project_inserts and 'active' in project_inserts[-1][1]


def test_guidance_on_active_project_is_noop_for_status(db):
    db.project_state = _project_row(status='active')
    ProjectModel.add_message(PROJECT_ID, 'user', 'guidance', 'FYI', user_id=USER_ID)
    assert not [
        c for c in db.mock.execute_insert.call_args_list
        if 'INSERT INTO project\n' in c.args[0]
    ]


# ---------------------------------------------------------------------------
# Plan checklist — insert-only
# ---------------------------------------------------------------------------

def test_task_add_then_check_writes_latest_row(db):
    task_id = ProjectModel.add_task(PROJECT_ID, 'Write migration', by=USER_ID)

    db.task_state = {'taskID': task_id, 'title': 'Write migration', 'done': 0,
                     'position': 0, 'note': None}
    assert ProjectModel.update_task(PROJECT_ID, task_id, done=True, by=USER_ID)

    task_inserts = [
        c.args[1] for c in db.mock.execute_insert.call_args_list
        if 'INSERT INTO project_task' in c.args[0]
    ]
    assert len(task_inserts) == 2
    assert task_inserts[0][2] == 'Write migration' and task_inserts[0][3] == 0
    assert task_inserts[1][3] == 1, 'toggled row must carry done=1'


def test_update_missing_task_returns_false(db):
    db.task_state = None
    assert ProjectModel.update_task(PROJECT_ID, 'nope', done=True) is False


# ---------------------------------------------------------------------------
# Message poll cursor
# ---------------------------------------------------------------------------

def test_list_messages_passes_cursor_and_parses(db):
    db.mock.execute_query.side_effect = lambda sql, params=None: [
        {'id': 7, 'messageID': 'm7', 'author': 'agent', 'kind': 'proposal',
         'body': None, 'meta': json.dumps({'title': 'Split'}),
         'resolution': None, 'created': None},
    ]
    rows = ProjectModel.list_messages(PROJECT_ID, since_id=5)
    called_sql, called_params = db.mock.execute_query.call_args.args
    assert called_params == (PROJECT_ID, 5)
    assert rows[0]['meta'] == {'title': 'Split'}


# ---------------------------------------------------------------------------
# Propose -> approve subproject
# ---------------------------------------------------------------------------

def test_approve_proposal_creates_linked_child_and_resolves(db):
    db.proposal_row = {
        'messageID': 'm9', 'projectID': PROJECT_ID, 'kind': 'proposal',
        'body': 'because reasons',
        'meta': json.dumps({'title': 'Data cleanup', 'description': 'CSV work'}),
        'resolution': None,
    }
    result = ProjectModel.resolve_proposal(USER_ID, 'm9', 'approve')

    assert result and result['parent_id'] == PROJECT_ID and result['child_id']

    child_insert = next(
        c.args[1] for c in db.mock.execute_insert.call_args_list
        if 'INSERT INTO project\n' in c.args[0]
    )
    # (projectID, userID, parentID, name, description, next_step, status, ...)
    assert child_insert[2] == PROJECT_ID
    assert child_insert[3] == 'Data cleanup'
    assert child_insert[6] == 'active'

    assert any(
        "resolution = 'approved'" in c.args[0]
        for c in db.mock.execute_update.call_args_list
    )


def test_approve_already_resolved_proposal_returns_none(db):
    db.proposal_row = {
        'messageID': 'm9', 'projectID': PROJECT_ID, 'kind': 'proposal',
        'body': '', 'meta': None, 'resolution': 'dismissed',
    }
    assert ProjectModel.resolve_proposal(USER_ID, 'm9', 'approve') is None
