"""
Unit tests: Triage email -> todo / project routing
=================================================
Why this matters:

* A converted email must be recorded in the `triage` table so it drops off the
  list on the next load — and recording it twice (double-click, retry) must not
  create duplicate rows.
* `ProjectModel.create` (used by the email->project action) must produce a
  normal top-level project: status 'active', no parent, position after the last.

DB access is mocked; no live database.

Run: pytest test/test_triage.py -v
"""

from unittest.mock import MagicMock

import pytest

from app.models.project_model import ProjectModel
from app.routes import triage


USER_ID = 'u-1'


@pytest.fixture
def db(monkeypatch):
    mock = MagicMock()
    mock.execute_insert.side_effect = lambda sql, params=None: 1
    mock.execute_update.side_effect = lambda sql, params=None: 1
    mock.execute_query.side_effect = lambda sql, params=None: []
    mock.execute_one.side_effect = lambda sql, params=None: None
    monkeypatch.setattr('app.models.project_model.db_manager', mock)
    monkeypatch.setattr('app.routes.triage.db_manager', mock)
    return mock


# ---------------------------------------------------------------------------
# triage: handled-email bookkeeping
# ---------------------------------------------------------------------------

def test_get_triaged_ids_returns_set(db):
    db.execute_query.side_effect = lambda sql, params=None: [
        {'gmailID': 'a'}, {'gmailID': 'b'},
    ]
    assert triage._get_triaged_ids(USER_ID) == {'a', 'b'}


def test_mark_triaged_inserts_once(db):
    db.execute_query.side_effect = lambda sql, params=None: []   # nothing handled yet
    triage._mark_triaged(USER_ID, 'msg-1')
    assert db.execute_insert.call_count == 1
    sql, params = db.execute_insert.call_args.args
    assert 'INSERT INTO triage' in sql
    assert params[1] == USER_ID and params[2] == 'msg-1'


def test_mark_triaged_skips_when_already_handled(db):
    db.execute_query.side_effect = lambda sql, params=None: [{'gmailID': 'msg-1'}]
    triage._mark_triaged(USER_ID, 'msg-1')
    assert db.execute_insert.call_count == 0


# ---------------------------------------------------------------------------
# ProjectModel.create (email -> project)
# ---------------------------------------------------------------------------

def test_project_create_makes_active_toplevel_project(db):
    db.execute_one.side_effect = lambda sql, params=None: {'m': 4}  # last position

    pid = ProjectModel.create(USER_ID, 'Roof repair', 'Contractor quote attached')

    assert isinstance(pid, str) and pid
    sql, params = db.execute_insert.call_args.args
    assert 'INSERT INTO project' in sql
    # (projectID, userID, parentID, name, description, next_step, status, position, ...)
    assert params[1] == USER_ID
    assert params[2] is None                    # parentID
    assert params[3] == 'Roof repair'
    assert params[4] == 'Contractor quote attached'
    assert params[6] == 'active'                # status
    assert params[7] == 5                       # position = max + 1


def test_project_create_position_zero_when_no_projects(db):
    db.execute_one.side_effect = lambda sql, params=None: {'m': None}
    ProjectModel.create(USER_ID, 'First project')
    _, params = db.execute_insert.call_args.args
    assert params[7] == 0


def test_project_create_truncates_long_name(db):
    db.execute_one.side_effect = lambda sql, params=None: {'m': None}
    ProjectModel.create(USER_ID, 'x' * 400)
    _, params = db.execute_insert.call_args.args
    assert len(params[3]) == 255
