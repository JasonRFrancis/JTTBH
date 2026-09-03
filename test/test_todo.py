"""
Unit Tests: Todo Model
======================
Tests for TodoModel methods using mocked database calls.

All database interactions are patched via unittest.mock so that no live
database connection is required.

Run with:
    pytest test/test_todo.py -v
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock, call

from test.synthetic import (
    TEST_USER,
    SYNTHETIC_TODOS,
    get_synthetic_todos,
    today,
    yesterday,
    tomorrow,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user_id():
    return TEST_USER['userID']


@pytest.fixture
def daily_todos(user_id):
    """Return synthetic daily todos for today."""
    return get_synthetic_todos(user_id=user_id, due=today, list_type='daily')


# ---------------------------------------------------------------------------
# Import guard
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_db(monkeypatch):
    """
    Patch db_manager at the module level so no DB connection is attempted.
    Each test overrides the return values it needs.
    """
    mock = MagicMock()
    monkeypatch.setattr('app.services.database.db_manager', mock)
    monkeypatch.setattr('app.models.todo_model.db_manager', mock)
    return mock


# ---------------------------------------------------------------------------
# TestTodoModel
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestTodoModelCreate:
    """Tests for TodoModel.create()"""

    def test_create_returns_todo_id(self, mock_db):
        """create() should return a non-empty UUID string."""
        from app.models.todo_model import TodoModel

        mock_db.execute_insert.return_value = 42

        todo_id = TodoModel.create(
            user_id=TEST_USER['userID'],
            title='Test todo',
            due=today,
            list_type='daily',
        )

        assert isinstance(todo_id, str)
        assert len(todo_id) == 36  # UUID format
        mock_db.execute_insert.assert_called_once()

    def test_create_inserts_correct_fields(self, mock_db):
        """create() INSERT should pass title, list_type, due, and user_id."""
        from app.models.todo_model import TodoModel

        mock_db.execute_insert.return_value = 1

        TodoModel.create(
            user_id=TEST_USER['userID'],
            title='Buy groceries',
            due=today,
            list_type='daily',
        )

        args = mock_db.execute_insert.call_args
        sql, params = args[0]
        assert 'INSERT INTO todo' in sql
        assert 'Buy groceries' in params

    def test_create_with_optional_fields(self, mock_db):
        """create() should accept and store optional content and list_name."""
        from app.models.todo_model import TodoModel

        mock_db.execute_insert.return_value = 1

        TodoModel.create(
            user_id=TEST_USER['userID'],
            title='Custom list item',
            due=None,
            list_type='custom',
            list_name='Work',
            position=3,
            content='Some notes here',
        )

        args = mock_db.execute_insert.call_args
        sql, params = args[0]
        assert 'INSERT INTO todo' in sql
        assert 'Work' in params
        assert 'Some notes here' in params


@pytest.mark.unit
class TestTodoModelRead:
    """Tests for TodoModel read methods."""

    def test_get_daily_todos_returns_list(self, mock_db):
        """get_daily_todos() should return a list of dicts."""
        from app.models.todo_model import TodoModel

        mock_db.execute_query.return_value = get_synthetic_todos(due=today, list_type='daily')

        result = TodoModel.get_daily_todos(TEST_USER['userID'], today)

        assert isinstance(result, list)
        mock_db.execute_query.assert_called_once()

    def test_get_daily_todos_filters_deleted(self, mock_db):
        """get_daily_todos() SQL should filter out title=NULL rows."""
        from app.models.todo_model import TodoModel

        mock_db.execute_query.return_value = []
        TodoModel.get_daily_todos(TEST_USER['userID'], today)

        sql = mock_db.execute_query.call_args[0][0]
        assert 'title IS NOT NULL' in sql or 'title IS NOT NULL' in sql.upper().replace('ISNOT', 'IS NOT')

    def test_get_todo_by_id_returns_none_when_not_found(self, mock_db):
        """get_todo_by_id() should return None when the todo does not exist."""
        from app.models.todo_model import TodoModel

        mock_db.execute_one.return_value = None

        result = TodoModel.get_todo_by_id('nonexistent-id', TEST_USER['userID'])

        assert result is None

    def test_get_todo_by_id_returns_dict(self, mock_db):
        """get_todo_by_id() should return the first matching todo dict."""
        from app.models.todo_model import TodoModel

        expected = SYNTHETIC_TODOS[0]
        mock_db.execute_one.return_value = expected

        result = TodoModel.get_todo_by_id(expected['todoID'], TEST_USER['userID'])

        assert result is expected

    def test_search_calls_db_with_query(self, mock_db):
        """search() should pass the query string to the database."""
        from app.models.todo_model import TodoModel

        mock_db.execute_query.return_value = []
        TodoModel.search(TEST_USER['userID'], 'test query')

        call_args = mock_db.execute_query.call_args
        assert call_args is not None
        # The search term (with LIKE wildcards or passed as param) should appear
        params = call_args[0][1]
        assert any('test query' in str(p) for p in params)


@pytest.mark.unit
class TestTodoModelToggle:
    """Tests for TodoModel.toggle_complete()"""

    def test_toggle_uncompleted_todo_sets_completed(self, mock_db):
        """Toggling an incomplete todo should insert a new row with completed=now."""
        from app.models.todo_model import TodoModel

        incomplete = dict(SYNTHETIC_TODOS[0])  # todo-001, completed=None
        incomplete['completed'] = None
        mock_db.execute_one.return_value = incomplete
        mock_db.execute_insert.return_value = 1

        TodoModel.toggle_complete(incomplete['todoID'], TEST_USER['userID'])

        mock_db.execute_insert.assert_called_once()
        args = mock_db.execute_insert.call_args[0]
        sql, params = args
        # completed value should be a datetime (not None)
        completed_param = None
        for p in params:
            if isinstance(p, datetime):
                completed_param = p
                break
        assert completed_param is not None, "Expected a datetime for completed field"

    def test_toggle_completed_todo_clears_completed(self, mock_db):
        """Toggling a completed todo should insert a new row with completed=None."""
        from app.models.todo_model import TodoModel

        completed = dict(SYNTHETIC_TODOS[1])  # todo-002, completed=datetime
        completed['completed'] = datetime.now()
        mock_db.execute_one.return_value = completed
        mock_db.execute_insert.return_value = 1

        TodoModel.toggle_complete(completed['todoID'], TEST_USER['userID'])

        mock_db.execute_insert.assert_called_once()
        args = mock_db.execute_insert.call_args[0]
        sql, params = args
        # None should appear in params (the cleared completed field)
        assert None in params, "Expected None in params for cleared completed field"


@pytest.mark.unit
class TestTodoModelDelete:
    """Tests for TodoModel.delete() (soft-delete via INSERT NULL title)."""

    def test_soft_delete_inserts_null_title(self, mock_db):
        """delete() should insert a new row with title=NULL."""
        from app.models.todo_model import TodoModel

        todo = SYNTHETIC_TODOS[0]
        mock_db.execute_one.return_value = todo
        mock_db.execute_insert.return_value = 1

        TodoModel.delete(todo['todoID'], TEST_USER['userID'])

        mock_db.execute_insert.assert_called_once()
        args = mock_db.execute_insert.call_args[0]
        sql, params = args
        assert None in params, "Expected None (NULL title) in INSERT params"
        assert 'INSERT INTO todo' in sql


@pytest.mark.unit
class TestTodoModelPushForward:
    """Tests for push-forward logic."""

    def test_push_forward_check_queries_correct_date(self, mock_db):
        """push_forward_check() should query todo_pushedForward for today."""
        from app.models.todo_model import TodoModel

        mock_db.execute_one.return_value = None

        TodoModel.push_forward_check(TEST_USER['userID'], today)

        call_args = mock_db.execute_one.call_args[0]
        params = call_args[1]
        assert today in params or str(today) in str(params)

    def test_push_forward_returns_integer_count(self, mock_db):
        """push_forward() should return the number of items pushed forward."""
        from app.models.todo_model import TodoModel

        # Simulate 3 incomplete yesterday todos
        incomplete_todos = [
            {**SYNTHETIC_TODOS[0], 'due': yesterday, 'completed': None},
            {**SYNTHETIC_TODOS[0], 'todoID': 'todo-x1', 'due': yesterday, 'completed': None},
            {**SYNTHETIC_TODOS[0], 'todoID': 'todo-x2', 'due': yesterday, 'completed': None},
        ]
        mock_db.execute_query.return_value = incomplete_todos
        mock_db.execute_one.return_value = None  # nothing already pushed today
        mock_db.execute_insert.return_value = 1

        count = TodoModel.push_forward(TEST_USER['userID'], today)

        assert isinstance(count, int)
        assert count >= 0

    def test_push_forward_moves_items_straight_to_someday_soon(self, mock_db):
        """
        A previous-day carry-over must land directly in the Someday Soon
        planning list -- it should never stop in today's daily list first.
        This encodes the annoyances.md decision to drop the old
        "one free day, then Someday" grace period.
        """
        from app.models.todo_model import TodoModel

        incomplete_todos = [
            {**SYNTHETIC_TODOS[0], 'due': yesterday, 'completed': None},
        ]
        mock_db.execute_query.return_value = incomplete_todos
        mock_db.execute_one.return_value = None  # not already pushed today
        mock_db.execute_insert.return_value = 1

        TodoModel.push_forward(TEST_USER['userID'], today)

        # First execute_insert call is the new `todo` row for the carry-over
        insert_sql, insert_params = mock_db.execute_insert.call_args_list[0][0]
        assert 'INSERT INTO todo' in insert_sql
        # Params order: todoID, userID, title, content, due, list_type,
        #                list_name, position, added, created_by
        due, list_type, list_name = insert_params[4], insert_params[5], insert_params[6]
        assert due is None, "carried-over todo must not be re-dated to today"
        assert list_type == 'planning'
        assert list_name == 'someday_soon'


@pytest.mark.unit
class TestTodoModelReorder:
    """Tests for TodoModel.reorder()"""

    def test_reorder_calls_update_for_each_item(self, mock_db):
        """reorder() should update positions for each todo in the list."""
        from app.models.todo_model import TodoModel

        mock_db.execute_insert.return_value = 1

        todo_ids = ['todo-001', 'todo-002', 'todo-003']
        positions = [0, 1, 2]

        TodoModel.reorder(TEST_USER['userID'], todo_ids, positions)

        # Should have called execute_insert or execute_update at least len(todo_ids) times
        total_calls = mock_db.execute_insert.call_count + mock_db.execute_update.call_count
        assert total_calls >= len(todo_ids)
