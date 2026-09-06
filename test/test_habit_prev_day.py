"""
Unit tests: previous-day habit catch-up grid
============================================
Why this matters:

* An untouched habit and a habit you actively skipped must be distinguishable —
  the dashboard needs to know which of yesterday's habits still need an answer.
* The cycle order Jason specified is complete -> not completed -> unresolved,
  i.e. from the untouched state: NULL -> 1 -> 0 -> NULL.
* A retried request (same change_id) must not double-write.
* The dashboard only shows the catch-up panel while something is unresolved.

DB access is mocked; no live database.

Run: pytest test/test_habit_prev_day.py -v
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.models.habit_model import HabitModel
from app.routes import dashboard as dash


HABIT_ID = 'h-1'
USER_ID = 'u-1'
YESTERDAY = date(2026, 9, 5)


@pytest.fixture
def db(monkeypatch):
    mock = MagicMock()

    def execute_one(sql, params=None):
        if 'WHERE change_id' in sql:
            return db.dedup_row
        if 'FROM habit h' in sql:
            return {'habitID': HABIT_ID, 'name': 'Read', 'dayweek': 127}
        if 'FROM habit_entry he' in sql:
            return db.current_entry
        return None

    mock.execute_one.side_effect = execute_one
    mock.execute_insert.side_effect = lambda sql, params=None: 1
    monkeypatch.setattr('app.models.habit_model.db_manager', mock)

    db.mock = mock
    db.dedup_row = None
    db.current_entry = None
    return db


def _inserted_completed(mock):
    """The `completed` value from the single habit_entry INSERT (params[2])."""
    calls = [c for c in mock.execute_insert.call_args_list
             if 'INSERT INTO habit_entry' in c.args[0]]
    assert len(calls) == 1
    return calls[0].args[1][2]


# ---------------------------------------------------------------------------
# cycle_entry ring: NULL -> 1 -> 0 -> NULL
# ---------------------------------------------------------------------------

def test_cycle_from_unresolved_marks_complete(db):
    db.current_entry = None
    assert HabitModel.cycle_entry(HABIT_ID, USER_ID, YESTERDAY)['completed'] == 1
    assert _inserted_completed(db.mock) == 1


def test_cycle_from_complete_marks_not_completed(db):
    db.current_entry = {'completed': 1}
    assert HabitModel.cycle_entry(HABIT_ID, USER_ID, YESTERDAY)['completed'] == 0
    assert _inserted_completed(db.mock) == 0


def test_cycle_from_not_completed_marks_unresolved(db):
    db.current_entry = {'completed': 0}
    assert HabitModel.cycle_entry(HABIT_ID, USER_ID, YESTERDAY)['completed'] is None
    assert _inserted_completed(db.mock) is None


def test_duplicate_change_id_does_not_rewrite(db):
    db.dedup_row = {'completed': 1}
    result = HabitModel.cycle_entry(HABIT_ID, USER_ID, YESTERDAY, change_id='dup')
    assert result == {'completed': 1}
    assert not db.mock.execute_insert.called


def test_cycle_unknown_habit_is_noop(db):
    # get_habit_by_id returns None -> nothing written
    db.mock.execute_one.side_effect = lambda sql, params=None: None
    assert HabitModel.cycle_entry('nope', USER_ID, YESTERDAY) == {'completed': None}
    assert not db.mock.execute_insert.called


# ---------------------------------------------------------------------------
# dashboard: panel visibility
# ---------------------------------------------------------------------------

def _cell(habit_id='h', applies=True, completed=None):
    return {'habitID': habit_id, 'applies': applies, 'completed': completed}


def test_prev_day_grid_counts_only_unresolved_applicable_cells(monkeypatch):
    monkeypatch.setattr(dash, 'user_today', lambda: date(2026, 9, 6))
    grid = [
        _cell('a', completed=None),   # unresolved  -> counts
        _cell('b', completed=1),      # complete     -> no
        _cell('c', completed=0),      # not completed -> no
        _cell('d', applies=False, completed=None),   # not scheduled -> no
        {'habitID': None, 'applies': False, 'completed': None},  # empty slot
    ]
    monkeypatch.setattr(HabitModel, 'get_grid_for_date', staticmethod(lambda uid, d: grid))

    out_grid, unresolved, day = dash._get_prev_day_habit_grid(USER_ID)
    assert day == date(2026, 9, 5)
    assert unresolved == 1
    assert out_grid is grid


def test_prev_day_grid_zero_when_all_resolved(monkeypatch):
    monkeypatch.setattr(dash, 'user_today', lambda: date(2026, 9, 6))
    grid = [_cell('a', completed=1), _cell('b', completed=0)]
    monkeypatch.setattr(HabitModel, 'get_grid_for_date', staticmethod(lambda uid, d: grid))
    _, unresolved, _ = dash._get_prev_day_habit_grid(USER_ID)
    assert unresolved == 0
