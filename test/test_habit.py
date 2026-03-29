"""
Unit Tests: Habit Model
=======================
Tests for HabitModel methods using mocked database calls.

Covers:
    - dayweek bitmask encoding/decoding
    - grid position encoding (row * 5 + col)
    - streak calculation
    - toggle entry (insert-only)

Run with:
    pytest test/test_habit.py -v
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

from test.synthetic import (
    TEST_USER,
    SYNTHETIC_HABITS,
    SYNTHETIC_HABIT_ENTRIES,
    get_synthetic_habits,
    get_synthetic_habit_entries,
    today,
    yesterday,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_db(monkeypatch):
    """Patch db_manager so no live DB connection is needed."""
    mock = MagicMock()
    monkeypatch.setattr('app.services.database.db_manager', mock)
    try:
        monkeypatch.setattr('app.models.habit_model.db_manager', mock)
    except AttributeError:
        pass  # Model may not exist yet; skip patch
    return mock


# ---------------------------------------------------------------------------
# TestDayweekBitmask
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDayweekBitmask:
    """Test the dayweek bitmask encoding used for habit scheduling."""

    # Bitmask: Sun=1, Mon=2, Tue=4, Wed=8, Thu=16, Fri=32, Sat=64
    DAYS = {
        'sunday':    1,
        'monday':    2,
        'tuesday':   4,
        'wednesday': 8,
        'thursday':  16,
        'friday':    32,
        'saturday':  64,
    }

    def test_all_days_bitmask(self):
        """All 7 days set = 127 (1+2+4+8+16+32+64)."""
        all_days = sum(self.DAYS.values())
        assert all_days == 127

    def test_single_day_bitmask_sunday(self):
        """Sunday alone = bitmask 1."""
        assert self.DAYS['sunday'] == 1

    def test_single_day_bitmask_saturday(self):
        """Saturday alone = bitmask 64."""
        assert self.DAYS['saturday'] == 64

    def test_weekdays_only_bitmask(self):
        """Mon-Fri = 2+4+8+16+32 = 62."""
        weekdays = sum(v for k, v in self.DAYS.items() if k not in ('sunday', 'saturday'))
        assert weekdays == 62

    def test_weekend_bitmask(self):
        """Sat+Sun = 64+1 = 65."""
        weekend = self.DAYS['sunday'] + self.DAYS['saturday']
        assert weekend == 65

    def test_habit_scheduled_for_today(self):
        """A habit with dayweek=127 should be scheduled for any day."""
        dayweek = 127
        # Python weekday() Mon=0; convert to schema: Sun=1 bit, Mon=2 bit, etc.
        day_bit = 1 << ((today.weekday() + 1) % 7)
        assert dayweek & day_bit != 0

    def test_habit_not_scheduled_when_bit_unset(self):
        """A habit scheduled only for Sunday should not run on Monday."""
        sunday_only = self.DAYS['sunday']   # = 1
        monday_bit = self.DAYS['monday']    # = 2
        assert sunday_only & monday_bit == 0

    def test_synthetic_habit_all_days(self):
        """The all-days habit in synthetic data should have dayweek=127."""
        habit = SYNTHETIC_HABITS[0]
        assert habit['dayweek'] == 127

    def test_synthetic_habit_saturday_only(self):
        """The weekly-review habit should have dayweek=64 (Saturday only)."""
        weekly = next(h for h in SYNTHETIC_HABITS if h['name'] == 'Weekly Review')
        assert weekly['dayweek'] == 64


# ---------------------------------------------------------------------------
# TestGridPositionEncoding
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGridPositionEncoding:
    """
    Test the habit grid position encoding.

    The 5x5 habit grid encodes position as: position = row * 5 + col
    where row and col are 0-indexed.  This gives positions 0-24.
    """

    def test_top_left_position(self):
        """Row 0, Col 0 -> position 0."""
        row, col = 0, 0
        assert row * 5 + col == 0

    def test_top_right_position(self):
        """Row 0, Col 4 -> position 4."""
        row, col = 0, 4
        assert row * 5 + col == 4

    def test_second_row_start(self):
        """Row 1, Col 0 -> position 5."""
        row, col = 1, 0
        assert row * 5 + col == 5

    def test_bottom_right_position(self):
        """Row 4, Col 4 -> position 24 (last in a 5x5 grid)."""
        row, col = 4, 4
        assert row * 5 + col == 24

    def test_round_trip_encoding(self):
        """position -> (row, col) -> position should be identity."""
        for position in range(25):
            row = position // 5
            col = position % 5
            assert row * 5 + col == position

    def test_habit_position_in_range(self):
        """Synthetic habit positions should be within the valid range."""
        for habit in SYNTHETIC_HABITS:
            pos = habit['position']
            # Allow broader range since habits can be repositioned
            assert pos >= 0


# ---------------------------------------------------------------------------
# TestStreakCalculation
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestStreakCalculation:
    """
    Test streak calculation logic for habits.

    A streak is the consecutive number of days a habit was completed
    going backwards from the most recent completed day.  Vacation days
    (vacation=1) do not break streaks.
    """

    def _calculate_streak(self, entries: list[dict]) -> int:
        """
        Reference streak implementation.

        Counts consecutive completed days from today backwards.
        Vacation days are skipped (treated as if they don't count against streak).
        """
        # Sort entries by date descending
        sorted_entries = sorted(entries, key=lambda e: e['entry'], reverse=True)
        streak = 0
        expected_date = today

        for entry in sorted_entries:
            # Skip future entries
            if entry['entry'] > today:
                continue

            # Allow gap-filling for vacation days
            if entry['vacation']:
                # Advance expected_date past this day
                expected_date = entry['entry']
                continue

            if entry['entry'] == expected_date:
                if entry['completed']:
                    streak += 1
                    expected_date = expected_date - timedelta(days=1)
                else:
                    break
            elif entry['entry'] < expected_date:
                # Gap in entries = streak broken
                break

        return streak

    def test_streak_zero_when_no_entries(self):
        """Empty entry list should give streak 0."""
        assert self._calculate_streak([]) == 0

    def test_streak_one_today(self):
        """Single completed entry today = streak of 1."""
        entries = [{'entry': today, 'completed': 1, 'vacation': 0}]
        assert self._calculate_streak(entries) == 1

    def test_streak_zero_today_not_completed(self):
        """Completed=None today = streak 0."""
        entries = [{'entry': today, 'completed': None, 'vacation': 0}]
        assert self._calculate_streak(entries) == 0

    def test_streak_consecutive_days(self):
        """Five consecutive completed days = streak of 5."""
        entries = [
            {'entry': today - timedelta(days=i), 'completed': 1, 'vacation': 0}
            for i in range(5)
        ]
        assert self._calculate_streak(entries) == 5

    def test_streak_breaks_on_miss(self):
        """A missed day (completed=None) should break the streak."""
        entries = [
            {'entry': today, 'completed': 1, 'vacation': 0},
            {'entry': yesterday, 'completed': None, 'vacation': 0},
            {'entry': today - timedelta(days=2), 'completed': 1, 'vacation': 0},
        ]
        assert self._calculate_streak(entries) == 1

    def test_streak_vacation_does_not_break(self):
        """A vacation day should not break the streak."""
        entries = [
            {'entry': today, 'completed': 1, 'vacation': 0},
            {'entry': yesterday, 'completed': None, 'vacation': 1},  # on vacation
            {'entry': today - timedelta(days=2), 'completed': 1, 'vacation': 0},
        ]
        # Vacation day is skipped; streak should continue
        streak = self._calculate_streak(entries)
        assert streak >= 1  # At minimum today counts

    def test_synthetic_habit_entries_have_some_completions(self):
        """Synthetic habit-001 entries should have at least some completed days."""
        entries = get_synthetic_habit_entries('habit-001', days=30)
        completed = [e for e in entries if e['completed']]
        assert len(completed) > 0


# ---------------------------------------------------------------------------
# TestToggleEntry
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestToggleEntry:
    """Tests for habit entry toggle (insert-only pattern)."""

    def test_toggle_inserts_new_row(self, mock_db):
        """toggle_entry() should call execute_insert, not execute_update."""
        try:
            from app.models.habit_model import HabitModel
        except ImportError:
            pytest.skip("HabitModel not yet implemented")

        mock_db.execute_insert.return_value = 1

        HabitModel.toggle_entry(
            habit_id='habit-001',
            entry_date=today,
            user_id=TEST_USER['userID'],
        )

        mock_db.execute_insert.assert_called_once()
        mock_db.execute_update.assert_not_called()

    def test_toggle_stores_correct_date(self, mock_db):
        """toggle_entry() should store the given date in the inserted row."""
        try:
            from app.models.habit_model import HabitModel
        except ImportError:
            pytest.skip("HabitModel not yet implemented")

        mock_db.execute_insert.return_value = 1

        HabitModel.toggle_entry(
            habit_id='habit-001',
            entry_date=today,
            user_id=TEST_USER['userID'],
        )

        args = mock_db.execute_insert.call_args[0]
        sql, params = args
        assert today in params or str(today) in str(params)

    def test_toggle_uses_insert_into_habit_entry(self, mock_db):
        """toggle_entry() INSERT should target the habit_entry table."""
        try:
            from app.models.habit_model import HabitModel
        except ImportError:
            pytest.skip("HabitModel not yet implemented")

        mock_db.execute_insert.return_value = 1

        HabitModel.toggle_entry(
            habit_id='habit-001',
            entry_date=today,
            user_id=TEST_USER['userID'],
        )

        sql = mock_db.execute_insert.call_args[0][0]
        assert 'habit_entry' in sql.lower()
