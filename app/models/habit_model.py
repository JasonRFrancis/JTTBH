"""
JTTBH Habit Model
=================
All database interactions for the habit feature.

Uses the insert-only pattern: to update a record, insert a new row with the
same habitID but updated field values.  To soft-delete, insert a new row with
name=NULL.  The current state of any habit is always the row with the highest
``id`` for a given ``habitID``.

Day-of-week bitmask (dayweek column):
    Sunday=1, Monday=2, Tuesday=4, Wednesday=8,
    Thursday=16, Friday=32, Saturday=64

Grid positions: 5x5 grid, row-major encoding.
    position = row * 5 + col
    position 0 = top-left (0,0), position 24 = bottom-right (4,4)

Public API
----------
    HabitModel.get_habits(user_id)                          -> list[dict]
    HabitModel.get_habit_by_id(habit_id, user_id)          -> dict | None
    HabitModel.create(user_id, name, ...)                   -> str  (habitID)
    HabitModel.update(habit_id, user_id, **fields)          -> None
    HabitModel.delete(habit_id, user_id)                    -> None
    HabitModel.get_entries(user_id, start_date, end_date)   -> list[dict]
    HabitModel.toggle_entry(habit_id, user_id, entry_date)  -> dict
    HabitModel.get_grid_for_date(user_id, entry_date)       -> list[dict]
    HabitModel.calculate_streaks(user_id)                   -> dict
    HabitModel.get_heatmap_data(user_id, days)              -> list[dict]
    HabitModel.get_calendar_data(user_id, ref_date)         -> list[dict]
    HabitModel.get_icons()                                  -> list[dict]
"""

import uuid
from datetime import date, datetime, timedelta

from app.services.database import db_manager


# ---------------------------------------------------------------------------
# Day-of-week bitmask constants
# ---------------------------------------------------------------------------

# Sunday=1, Monday=2, Tuesday=4, Wednesday=8, Thursday=16, Friday=32, Saturday=64
# Python's weekday(): Monday=0 … Sunday=6
# Python's isoweekday(): Monday=1 … Sunday=7
# To convert Python weekday() to our bitmask:
#   day_of_week = (weekday() + 1) % 7  -> 0=Sun, 1=Mon, ... 6=Sat
#   day_bit = 1 << day_of_week
_DOW_LABELS = {
    1:  'Sun',
    2:  'Mon',
    4:  'Tue',
    8:  'Wed',
    16: 'Thu',
    32: 'Fri',
    64: 'Sat',
}

_DOW_ALL = [1, 2, 4, 8, 16, 32, 64]


def _date_to_dow_bit(d: date) -> int:
    """Return the bitmask bit for the given date's day of week."""
    # Python weekday(): Monday=0 … Sunday=6
    # Our mapping: Sunday=1-bit-0, Monday=1-bit-1, ...
    day_of_week = (d.weekday() + 1) % 7   # 0=Sun, 1=Mon, ... 6=Sat
    return 1 << day_of_week


def dayweek_label(dayweek: int) -> str:
    """Return a human-readable string of active days from a bitmask."""
    if dayweek is None:
        return ''
    parts = [label for bit, label in _DOW_LABELS.items() if dayweek & bit]
    return ', '.join(parts)


class HabitModel:
    """Data-access layer for the habit feature."""

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_habits(user_id: str) -> list[dict]:
        """
        Return current state of all active habits for user_id.

        Only the most recent record per habitID is returned (highest id).
        Habits with name=NULL (soft-deleted) are excluded.

        Parameters
        ----------
        user_id : str
            The userID UUID.

        Returns
        -------
        list[dict]
            Each dict: habitID, name, description, action, color, icon,
            active, dayweek, position, vacation_mode.
        """
        sql = """
            SELECT h.habitID, h.name, h.description, h.action, h.color,
                   h.icon, h.active, h.dayweek, h.position, h.vacation_mode
            FROM habit h
            WHERE h.userID = %s
              AND h.id = (SELECT MAX(h2.id) FROM habit h2 WHERE h2.habitID = h.habitID)
              AND h.name IS NOT NULL
            ORDER BY h.position
        """
        return db_manager.execute_query(sql, (user_id,))

    @staticmethod
    def get_habit_by_id(habit_id: str, user_id: str) -> dict | None:
        """
        Return the current state of a single habit.

        Parameters
        ----------
        habit_id : str
            The habitID UUID.
        user_id : str
            Ownership check.

        Returns
        -------
        dict | None
        """
        sql = """
            SELECT h.habitID, h.name, h.description, h.action, h.color,
                   h.icon, h.active, h.dayweek, h.position, h.vacation_mode
            FROM habit h
            WHERE h.habitID = %s
              AND h.userID = %s
              AND h.id = (SELECT MAX(h2.id) FROM habit h2 WHERE h2.habitID = h.habitID)
              AND h.name IS NOT NULL
        """
        return db_manager.execute_one(sql, (habit_id, user_id))

    @staticmethod
    def get_entries(user_id: str, start_date: date, end_date: date) -> list[dict]:
        """
        Return the latest entry per habitID per date in a date range.

        Only considers habits belonging to user_id.

        Parameters
        ----------
        user_id : str
            The userID UUID.
        start_date : date
            Start of range (inclusive).
        end_date : date
            End of range (inclusive).

        Returns
        -------
        list[dict]
            Each dict: habitID, entry, completed, vacation, change_id.
        """
        sql = """
            SELECT he.habitID, he.entry, he.completed, he.vacation, he.change_id
            FROM habit_entry he
            WHERE he.habitID IN (
                SELECT DISTINCT h.habitID FROM habit h WHERE h.userID = %s
            )
              AND he.entry BETWEEN %s AND %s
              AND he.id = (
                  SELECT MAX(he2.id) FROM habit_entry he2
                  WHERE he2.habitID = he.habitID AND he2.entry = he.entry
              )
        """
        return db_manager.execute_query(sql, (user_id, start_date, end_date))

    @staticmethod
    def get_icons() -> list[dict]:
        """
        Return all available icons from the svg table.

        Returns
        -------
        list[dict]
            Each dict: imageID, name, description, svg.
        """
        sql = """
            SELECT imageID, name, description, svg
            FROM svg
            ORDER BY name
        """
        return db_manager.execute_query(sql)

    # ------------------------------------------------------------------
    # Write helpers (insert-only pattern)
    # ------------------------------------------------------------------

    @staticmethod
    def create(
        user_id: str,
        name: str,
        description: str = None,
        action: str = None,
        color: str = None,
        icon: str = None,
        active: int = 1,
        dayweek: int = 127,
        position: int = 0,
        vacation_mode: int = 1,
    ) -> str:
        """
        Insert a new habit row and return its habitID.

        A fresh UUID is generated as the habitID so the habit can be
        tracked through subsequent inserts (update/delete reuse it).

        Parameters
        ----------
        user_id : str
            The owning userID UUID.
        name : str
            Required habit name.
        description : str, optional
        action : str, optional
            Optional URL associated with the habit.
        color : str, optional
            Hex color string, e.g. '#2563eb'.
        icon : str, optional
            Icon name from the svg table.
        active : int
            1 = active, 0 = inactive.
        dayweek : int
            Bitmask of active days (default 127 = all days).
        position : int
            Grid position 0-24.
        vacation_mode : int
            1 = paused during vacation.

        Returns
        -------
        str
            The new habitID UUID string.
        """
        habit_id = str(uuid.uuid4())
        sql = """
            INSERT INTO habit (habitID, userID, name, description, action,
                               color, icon, active, dayweek, position,
                               vacation_mode, created, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """
        db_manager.execute_insert(sql, (
            habit_id, user_id, name, description, action,
            color, icon, active, dayweek, position,
            vacation_mode, user_id,
        ))
        return habit_id

    @staticmethod
    def update(habit_id: str, user_id: str, **fields) -> None:
        """
        Update a habit using the insert-only pattern.

        Fetches the current record, applies any overridden fields, and
        inserts a new row with the same habitID.

        Parameters
        ----------
        habit_id : str
            The habitID to update.
        user_id : str
            Ownership verification.
        **fields
            Any subset of: name, description, action, color, icon,
            active, dayweek, position, vacation_mode.
        """
        current = HabitModel.get_habit_by_id(habit_id, user_id)
        if current is None:
            return

        name         = fields.get('name',         current['name'])
        description  = fields.get('description',  current['description'])
        action       = fields.get('action',        current['action'])
        color        = fields.get('color',         current['color'])
        icon         = fields.get('icon',          current['icon'])
        active       = fields.get('active',        current['active'])
        dayweek      = fields.get('dayweek',       current['dayweek'])
        position     = fields.get('position',      current['position'])
        vacation_mode = fields.get('vacation_mode', current['vacation_mode'])

        sql = """
            INSERT INTO habit (habitID, userID, name, description, action,
                               color, icon, active, dayweek, position,
                               vacation_mode, created, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """
        db_manager.execute_insert(sql, (
            habit_id, user_id, name, description, action,
            color, icon, active, dayweek, position,
            vacation_mode, user_id,
        ))

    @staticmethod
    def delete(habit_id: str, user_id: str) -> None:
        """
        Soft-delete a habit by inserting a new record with name=NULL.

        Parameters
        ----------
        habit_id : str
            The habitID to delete.
        user_id : str
            Ownership verification.
        """
        current = HabitModel.get_habit_by_id(habit_id, user_id)
        if current is None:
            return

        sql = """
            INSERT INTO habit (habitID, userID, name, description, action,
                               color, icon, active, dayweek, position,
                               vacation_mode, created, created_by)
            VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """
        db_manager.execute_insert(sql, (
            habit_id, user_id,
            current['description'], current['action'],
            current['color'], current['icon'],
            current['active'], current['dayweek'],
            current['position'], current['vacation_mode'],
            user_id,
        ))

    @staticmethod
    def toggle_entry(habit_id: str, user_id: str, entry_date: date, change_id: str = None) -> dict:
        """
        Toggle the completion status for a habit on a given date.

        If no entry exists or completed=NULL, insert an entry with completed=1.
        If completed=1, insert an entry with completed=NULL.

        Parameters
        ----------
        habit_id : str
            The habitID to toggle.
        user_id : str
            Used for created_by; also verifies habit ownership.
        entry_date : date
            The date to toggle.
        change_id : str, optional
            Client-generated UUID for idempotency. If already stored, returns
            the existing state without re-toggling.

        Returns
        -------
        dict
            {'completed': 1} or {'completed': None}
        """
        # Idempotency: if we've already processed this change_id, return current state.
        if change_id:
            existing = db_manager.execute_one(
                "SELECT completed FROM habit_entry WHERE change_id = %s LIMIT 1",
                (change_id,),
            )
            if existing is not None:
                return {'completed': existing['completed']}

        # Verify the habit belongs to this user
        habit = HabitModel.get_habit_by_id(habit_id, user_id)
        if habit is None:
            return {'completed': None}

        # Get current entry state for this habit + date
        current_sql = """
            SELECT he.completed
            FROM habit_entry he
            WHERE he.habitID = %s
              AND he.entry = %s
            ORDER BY he.id DESC
            LIMIT 1
        """
        current = db_manager.execute_one(current_sql, (habit_id, entry_date))

        if current is None or current['completed'] is None:
            new_completed = 1
        else:
            new_completed = None

        insert_sql = """
            INSERT INTO habit_entry (habitID, entry, completed, change_id, created, created_by)
            VALUES (%s, %s, %s, %s, NOW(), %s)
        """
        db_manager.execute_insert(insert_sql, (habit_id, entry_date, new_completed, change_id, user_id))

        return {'completed': new_completed}

    # ------------------------------------------------------------------
    # Grid / calendar helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_grid_for_date(user_id: str, entry_date: date) -> list[dict]:
        """
        Build a 25-element grid (5x5) for a given date.

        Each element represents one grid position.  If a habit occupies
        that position and is scheduled for this date's day-of-week,
        the cell is populated.  Empty positions are represented with
        habitID=None.

        Parameters
        ----------
        user_id : str
            The userID UUID.
        entry_date : date
            The date to build the grid for.

        Returns
        -------
        list[dict]
            25 elements, each: {
                'position': 0-24,
                'habitID': None | str,
                'name': None | str,
                'color': None | str,
                'icon': None | str,
                'icon_svg': None | str,
                'completed': None | 1,
                'applies': bool,
            }
        """
        habits = HabitModel.get_habits(user_id)
        entries = HabitModel.get_entries(user_id, entry_date, entry_date)

        # Build lookup: habitID -> entry
        entry_map = {e['habitID']: e for e in entries}

        # Build lookup: habitID -> svg content (from svg table by icon name)
        icon_names = list({h['icon'] for h in habits if h.get('icon')})
        icon_svg_map = {}
        if icon_names:
            placeholders = ', '.join(['%s'] * len(icon_names))
            icon_rows = db_manager.execute_query(
                f'SELECT name, svg FROM svg WHERE name IN ({placeholders})',
                tuple(icon_names),
            )
            icon_svg_map = {row['name']: row['svg'] for row in icon_rows}

        # Determine day-of-week bit for this date
        dow_bit = _date_to_dow_bit(entry_date)

        # Collect all habits per position (multiple can share a position on non-overlapping days)
        position_habits: dict[int, list] = {}
        for habit in habits:
            pos = habit.get('position')
            if pos is None:
                continue
            position_habits.setdefault(pos, []).append(habit)

        # Build 25-element grid
        grid = []
        for pos in range(25):
            habits_here = position_habits.get(pos)
            if not habits_here:
                grid.append({
                    'position':  pos,
                    'habitID':   None,
                    'name':      None,
                    'color':     None,
                    'icon':      None,
                    'icon_svg':  None,
                    'completed': None,
                    'applies':   False,
                })
            else:
                # Prefer the habit that applies today; fall back to first if none do
                applying = next(
                    (h for h in habits_here if bool(h.get('dayweek', 0) & dow_bit)),
                    None,
                )
                habit  = applying if applying else habits_here[0]
                applies = applying is not None
                entry   = entry_map.get(habit['habitID'])
                completed = entry['completed'] if entry else None
                grid.append({
                    'position':  pos,
                    'habitID':   habit['habitID'],
                    'name':      habit['name'],
                    'color':     habit.get('color'),
                    'icon':      habit.get('icon'),
                    'icon_svg':  icon_svg_map.get(habit.get('icon', '')) if habit.get('icon') else None,
                    'completed': completed,
                    'applies':   applies,
                })
        return grid

    @staticmethod
    def calculate_streaks(user_id: str) -> dict:
        """
        Calculate current streak for each active habit.

        A streak is the number of consecutive days going backwards from
        yesterday (or today) where the habit was completed.  Vacation days
        are skipped for habits with vacation_mode=1.

        Parameters
        ----------
        user_id : str
            The userID UUID.

        Returns
        -------
        dict
            Mapping of habitID -> streak count (int).
        """
        habits = HabitModel.get_habits(user_id)
        if not habits:
            return {}

        # Fetch entries for the past 365 days
        today = date.today()
        start_date = today - timedelta(days=365)
        entries = HabitModel.get_entries(user_id, start_date, today)

        # Build lookup: (habitID, entry_date) -> completed
        entry_map: dict[tuple, int | None] = {}
        for e in entries:
            key = (e['habitID'], e['entry'])
            entry_map[key] = e['completed']

        # Fetch vacation periods for this user
        vacation_rows = db_manager.execute_query(
            'SELECT start, end FROM vacation WHERE userID = %s',
            (user_id,),
        )
        vacation_dates: set[date] = set()
        for vrow in vacation_rows:
            v_start = vrow['start']
            v_end   = vrow['end']
            if isinstance(v_start, str):
                v_start = date.fromisoformat(v_start)
            if isinstance(v_end, str):
                v_end = date.fromisoformat(v_end)
            current_v = v_start
            while current_v <= v_end:
                vacation_dates.add(current_v)
                current_v += timedelta(days=1)

        streaks: dict[str, int] = {}

        for habit in habits:
            habit_id     = habit['habitID']
            dayweek      = habit.get('dayweek', 0) or 0
            vac_mode     = habit.get('vacation_mode', 1)
            streak       = 0

            # Walk backwards from today
            check_date = today
            while check_date >= start_date:
                # Skip vacation days for habits with vacation_mode=1
                if vac_mode and check_date in vacation_dates:
                    check_date -= timedelta(days=1)
                    continue

                # Check if this habit applies on this day
                dow_bit = _date_to_dow_bit(check_date)
                if not (dayweek & dow_bit):
                    check_date -= timedelta(days=1)
                    continue

                # Check completion
                completed = entry_map.get((habit_id, check_date))
                if completed == 1:
                    streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break

            streaks[habit_id] = streak

        return streaks

    @staticmethod
    def get_heatmap_data(user_id: str, days: int = 365) -> list[dict]:
        """
        Return per-day habit completion data for the heatmap view.

        For each day in the range, counts how many habits apply that day
        and how many were completed.

        Parameters
        ----------
        user_id : str
            The userID UUID.
        days : int
            Number of days to include (counting back from today).

        Returns
        -------
        list[dict]
            Each dict: {
                'date': date,
                'total': int,     # habits that apply this day
                'completed': int, # habits completed
                'pct': float,     # 0.0 to 1.0
                'level': int,     # 0-4 heat level
            }
        """
        today      = date.today()
        start_date = today - timedelta(days=days - 1)

        habits  = HabitModel.get_habits(user_id)
        entries = HabitModel.get_entries(user_id, start_date, today)

        # Build entry lookup: (habitID, entry_date) -> completed
        entry_map: dict[tuple, int | None] = {}
        for e in entries:
            key = (e['habitID'], e['entry'])
            entry_map[key] = e['completed']

        result = []
        current = start_date
        while current <= today:
            dow_bit = _date_to_dow_bit(current)
            total     = 0
            completed = 0
            for habit in habits:
                dayweek = habit.get('dayweek', 0) or 0
                if dayweek & dow_bit:
                    total += 1
                    if entry_map.get((habit['habitID'], current)) == 1:
                        completed += 1

            pct = (completed / total) if total > 0 else 0.0

            # Assign heat level 0-4
            if pct == 0.0:
                level = 0
            elif pct <= 0.25:
                level = 1
            elif pct <= 0.50:
                level = 2
            elif pct <= 0.75:
                level = 3
            else:
                level = 4

            result.append({
                'date':      current,
                'total':     total,
                'completed': completed,
                'pct':       pct,
                'level':     level,
            })
            current += timedelta(days=1)

        return result

    @staticmethod
    def get_calendar_data(user_id: str, ref_date: date) -> list[dict]:
        """
        Return grid data for a 28-day window around ref_date.

        Window: 21 days before ref_date through 7 days after ref_date.

        Parameters
        ----------
        user_id : str
            The userID UUID.
        ref_date : date
            The reference date (typically today).

        Returns
        -------
        list[dict]
            28 elements, each: {
                'date': date,
                'is_today': bool,
                'grid': list[dict],  # 25-element grid from get_grid_for_date
            }
        """
        today      = date.today()
        sdays      = today.weekday() + 1
        start_date = ref_date - (timedelta(days=7) + timedelta(days=sdays))
        end_date   = ref_date + timedelta(days=13) - timedelta(days=sdays)

        habits  = HabitModel.get_habits(user_id)
        entries = HabitModel.get_entries(user_id, start_date, end_date)

        # Build entry lookup: (habitID, entry_date) -> completed
        entry_map: dict[tuple, int | None] = {}
        for e in entries:
            key = (e['habitID'], e['entry'])
            entry_map[key] = e['completed']

        # Build icon svg map
        icon_names = list({h['icon'] for h in habits if h.get('icon')})
        icon_svg_map: dict[str, str] = {}
        if icon_names:
            placeholders = ', '.join(['%s'] * len(icon_names))
            icon_rows = db_manager.execute_query(
                f'SELECT name, svg FROM svg WHERE name IN ({placeholders})',
                tuple(icon_names),
            )
            icon_svg_map = {row['name']: row['svg'] for row in icon_rows}

        # Build position map: position -> habit
        position_map: dict[int, dict] = {}
        for habit in habits:
            pos = habit.get('position')
            if pos is not None:
                position_map[pos] = habit

        result = []
        current = start_date
        while current <= end_date:
            dow_bit = _date_to_dow_bit(current)

            grid = []
            for pos in range(25):
                habit = position_map.get(pos)
                if habit is None:
                    grid.append({
                        'position':  pos,
                        'habitID':   None,
                        'name':      None,
                        'color':     None,
                        'icon':      None,
                        'icon_svg':  None,
                        'completed': None,
                        'applies':   False,
                    })
                else:
                    entry     = entry_map.get((habit['habitID'], current))
                    completed = entry if entry is not None else None
                    applies   = bool((habit.get('dayweek', 0) or 0) & dow_bit)
                    grid.append({
                        'position':  pos,
                        'habitID':   habit['habitID'],
                        'name':      habit['name'],
                        'color':     habit.get('color'),
                        'icon':      habit.get('icon'),
                        'icon_svg':  icon_svg_map.get(habit.get('icon', '')) if habit.get('icon') else None,
                        'completed': completed,
                        'applies':   applies,
                    })

            result.append({
                'date':     current,
                'is_today': current == today,
                'grid':     grid,
            })
            current += timedelta(days=1)

        return result
