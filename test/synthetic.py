"""
Synthetic Test Data
===================
Pre-built in-memory data structures for use in unit tests and development
without a live database connection.

Set SYNTHETIC_MODE = True to make model functions return synthetic data
instead of querying the database (requires model support for this mode).

Usage in tests
--------------
    from test.synthetic import SYNTHETIC_TODOS, get_synthetic_todos, TEST_USER
"""

from datetime import date, datetime, timedelta

# ---------------------------------------------------------------------------
# Control flag
# ---------------------------------------------------------------------------

#: Set to True to enable synthetic data mode (bypasses DB calls in models).
SYNTHETIC_MODE = False

# ---------------------------------------------------------------------------
# Reference dates
# ---------------------------------------------------------------------------

today = date.today()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)
last_week = today - timedelta(days=7)

# ---------------------------------------------------------------------------
# Test user
# ---------------------------------------------------------------------------

TEST_USER = {
    'userID': '-58ec8c11-e060-4367-93cf-91a6cc28db8c',  # Leading - marks test data
    'username': 'testuser',
    'email': 'test@example.com',
    'name': 'Test User',
    'approval_status': 'approved',
    'admin': 0,
    'active': 1,
    'perm_read': 8190,   # All permissions except admin
    'perm_write': 8190,
}

# ---------------------------------------------------------------------------
# Todos
# ---------------------------------------------------------------------------

SYNTHETIC_TODOS = [
    {
        'todoID': 'todo-001',
        'userID': TEST_USER['userID'],
        'title': 'Write unit tests',
        'content': 'Cover all model methods with mocked database',
        'due': today,
        'list_type': 'daily',
        'list_name': None,
        'position': 0,
        'completed': None,
        'added': today,
        'created': datetime.now(),
        'created_by': TEST_USER['userID'],
    },
    {
        'todoID': 'todo-002',
        'userID': TEST_USER['userID'],
        'title': 'Review pull request',
        'content': None,
        'due': today,
        'list_type': 'daily',
        'list_name': None,
        'position': 1,
        'completed': datetime.now(),
        'added': today,
        'created': datetime.now(),
        'created_by': TEST_USER['userID'],
    },
    {
        'todoID': 'todo-003',
        'userID': TEST_USER['userID'],
        'title': 'Refactor database layer',
        'content': 'Move to connection pooling for production',
        'due': None,
        'list_type': 'planning',
        'list_name': 'someday_soon',
        'position': 0,
        'completed': None,
        'added': last_week,
        'created': datetime(today.year, today.month, today.day) - timedelta(days=7),
        'created_by': TEST_USER['userID'],
    },
    {
        'todoID': 'todo-004',
        'userID': TEST_USER['userID'],
        'title': 'Deploy to production',
        'content': None,
        'due': tomorrow,
        'list_type': 'daily',
        'list_name': None,
        'position': 0,
        'completed': None,
        'added': today,
        'created': datetime.now(),
        'created_by': TEST_USER['userID'],
    },
    {
        'todoID': 'todo-deleted',
        'userID': TEST_USER['userID'],
        'title': None,  # NULL = soft-deleted in insert-only pattern
        'content': None,
        'due': yesterday,
        'list_type': 'daily',
        'list_name': None,
        'position': 2,
        'completed': None,
        'added': yesterday,
        'created': datetime.now(),
        'created_by': TEST_USER['userID'],
    },
]

# ---------------------------------------------------------------------------
# Habits
# ---------------------------------------------------------------------------

SYNTHETIC_HABITS = [
    {
        'habitID': 'habit-001',
        'userID': TEST_USER['userID'],
        'name': 'Morning Exercise',
        'description': '30 min workout',
        'icon': 'exercise',
        'color': '#4caf50',
        'action': None,
        'position': 0,
        'dayweek': 127,  # All 7 days (bitmask: 1+2+4+8+16+32+64)
        'active': 1,
        'vacation_mode': 1,
    },
    {
        'habitID': 'habit-002',
        'userID': TEST_USER['userID'],
        'name': 'Read 30 Minutes',
        'description': 'Non-fiction or technical reading',
        'icon': 'book',
        'color': '#2196f3',
        'action': None,
        'position': 1,
        'dayweek': 127,  # All days
        'active': 1,
        'vacation_mode': 0,  # Not paused during vacation
    },
    {
        'habitID': 'habit-003',
        'userID': TEST_USER['userID'],
        'name': 'Weekly Review',
        'description': 'GTD weekly review',
        'icon': 'review',
        'color': '#ff9800',
        'action': None,
        'position': 2,
        'dayweek': 64,  # Saturday only (bit 6 = 64)
        'active': 1,
        'vacation_mode': 1,
    },
    {
        'habitID': 'habit-inactive',
        'userID': TEST_USER['userID'],
        'name': 'Old Habit',
        'description': 'Deactivated habit',
        'icon': None,
        'color': None,
        'action': None,
        'position': 10,
        'dayweek': 127,
        'active': 0,
        'vacation_mode': 1,
    },
]

# ---------------------------------------------------------------------------
# Habit entries (last 30 days for habit-001)
# ---------------------------------------------------------------------------

SYNTHETIC_HABIT_ENTRIES = [
    {
        'habitID': 'habit-001',
        'entry': today - timedelta(days=i),
        'completed': None if (i % 4 == 0) else 1,  # Miss every 4th day
        'vacation': 0,
        'created': datetime.now() - timedelta(days=i),
        'created_by': TEST_USER['userID'],
    }
    for i in range(30)
]

# Add some vacation entries
SYNTHETIC_HABIT_ENTRIES += [
    {
        'habitID': 'habit-001',
        'entry': today - timedelta(days=i),
        'completed': None,
        'vacation': 1,
        'created': datetime.now() - timedelta(days=i),
        'created_by': TEST_USER['userID'],
    }
    for i in range(14, 18)  # 4-day vacation window
]

# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

SYNTHETIC_PROJECTS = [
    {
        'projectID': 'proj-001',
        'userID': TEST_USER['userID'],
        'name': 'JTTBH Application',
        'description': 'Build the Just Trying to be Helpful personal productivity app',
        'next_step': 'Write unit tests for all models',
        'position': 0,
    },
    {
        'projectID': 'proj-002',
        'userID': TEST_USER['userID'],
        'name': 'Home Network Upgrade',
        'description': 'Replace aging router and add wired ethernet drops',
        'next_step': 'Research mesh network options',
        'position': 1,
    },
]

SYNTHETIC_PROJECT_RESOURCES = [
    {
        'resourceID': 'res-001',
        'projectID': 'proj-001',
        'name': 'GitHub Repository',
        'resource': 'https://github.com/JasonRFrancis/JTTBH',
        'note': 'Main source repository',
        'position': 0,
    },
    {
        'resourceID': 'res-002',
        'projectID': 'proj-001',
        'name': 'Specification',
        'resource': 'SPECIFICATION.md',
        'note': 'Full project specification',
        'position': 1,
    },
]

# ---------------------------------------------------------------------------
# Books
# ---------------------------------------------------------------------------

SYNTHETIC_BOOKS = [
    {
        'bookID': 'book-001',
        'userID': TEST_USER['userID'],
        'title': 'Getting Things Done',
        'author': 'David Allen',
        'isbn': '9780143126560',
        'pages': 352,
        'tags': 'productivity, gtd',
        'cover': None,
        'status': 'completed',
        'rating': 5,
        'review': 'Essential reading for productivity.',
        'notes': None,
        'started': today - timedelta(days=60),
        'finished': today - timedelta(days=10),
    },
    {
        'bookID': 'book-002',
        'userID': TEST_USER['userID'],
        'title': 'The Pragmatic Programmer',
        'author': 'David Thomas, Andrew Hunt',
        'isbn': '9780135957059',
        'pages': 352,
        'tags': 'programming, career',
        'cover': None,
        'status': 'reading',
        'rating': None,
        'review': None,
        'notes': 'Taking notes as I read.',
        'started': today - timedelta(days=14),
        'finished': None,
    },
    {
        'bookID': 'book-003',
        'userID': TEST_USER['userID'],
        'title': 'Atomic Habits',
        'author': 'James Clear',
        'isbn': '9780735211292',
        'pages': 320,
        'tags': 'habits, psychology',
        'cover': None,
        'status': 'want_to_read',
        'rating': None,
        'review': None,
        'notes': None,
        'started': None,
        'finished': None,
    },
]

# ---------------------------------------------------------------------------
# Bookmarks
# ---------------------------------------------------------------------------

SYNTHETIC_BOOKMARKS = [
    {
        'bookmarkID': 'bm-001',
        'userID': TEST_USER['userID'],
        'url': 'https://flask.palletsprojects.com/',
        'title': 'Flask Documentation',
        'description': 'The official Flask web framework documentation.',
        'tags': 'python, flask, web',
        'read_later': 0,
        'read': 1,
        'notes': None,
        'favicon': None,
        'created': datetime.now() - timedelta(days=3),
    },
    {
        'bookmarkID': 'bm-002',
        'userID': TEST_USER['userID'],
        'url': 'https://docs.pytest.org/',
        'title': 'pytest Documentation',
        'description': 'pytest testing framework docs.',
        'tags': 'python, testing',
        'read_later': 1,
        'read': 0,
        'notes': 'Read before writing tests',
        'favicon': None,
        'created': datetime.now() - timedelta(days=1),
    },
]

# ---------------------------------------------------------------------------
# Vacation periods
# ---------------------------------------------------------------------------

SYNTHETIC_VACATIONS = [
    {
        'id': 1,
        'userID': TEST_USER['userID'],
        'name': 'Summer Vacation',
        'start': today - timedelta(days=60),
        'end': today - timedelta(days=53),
        'description': 'Beach trip',
        'created': datetime.now() - timedelta(days=70),
    },
]

# ---------------------------------------------------------------------------
# Filter helpers
# ---------------------------------------------------------------------------

def get_synthetic_todos(
    user_id: str | None = None,
    due: date | None = None,
    list_type: str | None = None,
    include_deleted: bool = False,
) -> list[dict]:
    """
    Return filtered synthetic todos.

    Parameters
    ----------
    user_id        : str | None   Filter by userID.
    due            : date | None  Filter by due date.
    list_type      : str | None   Filter by list_type.
    include_deleted: bool         Include rows with title=None (deleted).
    """
    todos = SYNTHETIC_TODOS
    if not include_deleted:
        todos = [t for t in todos if t['title'] is not None]
    if user_id:
        todos = [t for t in todos if t['userID'] == user_id]
    if due is not None:
        todos = [t for t in todos if t['due'] == due]
    if list_type:
        todos = [t for t in todos if t['list_type'] == list_type]
    return todos


def get_synthetic_habits(user_id: str | None = None, active_only: bool = True) -> list[dict]:
    """Return filtered synthetic habits."""
    habits = SYNTHETIC_HABITS
    if user_id:
        habits = [h for h in habits if h['userID'] == user_id]
    if active_only:
        habits = [h for h in habits if h['active'] == 1]
    return habits


def get_synthetic_habit_entries(habit_id: str, days: int = 30) -> list[dict]:
    """Return synthetic habit entries for a given habit over the last N days."""
    cutoff = today - timedelta(days=days)
    return [
        e for e in SYNTHETIC_HABIT_ENTRIES
        if e['habitID'] == habit_id and e['entry'] >= cutoff
    ]


def get_synthetic_books(user_id: str | None = None, status: str | None = None) -> list[dict]:
    """Return filtered synthetic books."""
    books = SYNTHETIC_BOOKS
    if user_id:
        books = [b for b in books if b['userID'] == user_id]
    if status:
        books = [b for b in books if b['status'] == status]
    return books
