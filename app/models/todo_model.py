"""
Todo Model
==========
All database interactions for the todo feature.

Uses the insert-only pattern: to update a record, insert a new row with the
same todoID but updated field values.  To soft-delete, insert a new row with
title=NULL.  The current state of any todo is always the row with the highest
``id`` for a given ``todoID``.

Public API
----------
    TodoModel.get_daily_todos(user_id, date)        -> list[dict]
    TodoModel.get_custom_todos(user_id, list_name)  -> list[dict]
    TodoModel.get_planning_todos(user_id, list_name)-> list[dict]
    TodoModel.create(...)                           -> str  (todoID)
    TodoModel.update(...)                           -> None
    TodoModel.delete(todo_id, user_id)              -> None
    TodoModel.toggle_complete(todo_id, user_id)     -> None
    TodoModel.move(...)                             -> None
    TodoModel.push_forward_check(user_id, today)    -> bool
    TodoModel.push_forward(user_id, today)          -> int
    TodoModel.get_todo_by_id(todo_id, user_id)      -> dict | None
    TodoModel.search(user_id, query)                -> list[dict]
    TodoModel.reorder(user_id, todo_ids, positions) -> None
    TodoModel.get_all_lists(user_id)                -> dict
"""

import uuid
from datetime import date, datetime, timedelta

from app.services.database import db_manager


class TodoModel:
    """Data-access layer for the todo feature."""

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_daily_todos(user_id: str, for_date: date) -> list[dict]:
        """
        Return all active (non-deleted) daily todo items for *user_id* on
        *for_date*, ordered by position then creation time.

        Parameters
        ----------
        user_id : str
            The userID UUID of the authenticated user.
        for_date : date
            The calendar date to query.

        Returns
        -------
        list[dict]
            Each dict contains: todoID, title, content, due, list_type,
            list_name, position, completed, added.
        """
        sql = """
            SELECT t.todoID, t.title, t.content, t.due, t.list_type,
                   t.list_name, t.position, t.completed, t.added
            FROM todo t
            WHERE t.userID = %s
              AND t.due = %s
              AND t.list_type = 'daily'
              AND t.id = (
                  SELECT MAX(t2.id) FROM todo t2 WHERE t2.todoID = t.todoID
              )
              AND t.title IS NOT NULL
            ORDER BY t.position, t.created
        """
        return db_manager.execute_query(sql, (user_id, for_date))

    @staticmethod
    def get_custom_todos(user_id: str, list_name: str) -> list[dict]:
        """
        Return all active custom list items for *user_id* with *list_name*.

        Parameters
        ----------
        user_id : str
            The userID UUID.
        list_name : str
            The custom list name (matches list_name column, list_type='custom').

        Returns
        -------
        list[dict]
        """
        sql = """
            SELECT t.todoID, t.title, t.content, t.due, t.list_type,
                   t.list_name, t.position, t.completed, t.added
            FROM todo t
            WHERE t.userID = %s
              AND t.list_type = 'custom'
              AND t.list_name = %s
              AND t.id = (
                  SELECT MAX(t2.id) FROM todo t2 WHERE t2.todoID = t.todoID
              )
              AND t.title IS NOT NULL
            ORDER BY t.position, t.created
        """
        return db_manager.execute_query(sql, (user_id, list_name))

    @staticmethod
    def get_planning_todos(user_id: str, list_name: str) -> list[dict]:
        """
        Return all active planning list items for *user_id* with *list_name*.

        Parameters
        ----------
        user_id : str
            The userID UUID.
        list_name : str
            One of: 'next_week', 'this_month', 'next_month', 'someday_soon'.

        Returns
        -------
        list[dict]
        """
        sql = """
            SELECT t.todoID, t.title, t.content, t.due, t.list_type,
                   t.list_name, t.position, t.completed, t.added
            FROM todo t
            WHERE t.userID = %s
              AND t.list_type = 'planning'
              AND t.list_name = %s
              AND t.id = (
                  SELECT MAX(t2.id) FROM todo t2 WHERE t2.todoID = t.todoID
              )
              AND t.title IS NOT NULL
            ORDER BY t.position, t.created
        """
        return db_manager.execute_query(sql, (user_id, list_name))

    @staticmethod
    def get_todo_by_id(todo_id: str, user_id: str) -> dict | None:
        """
        Return the current state of a single todo item.

        Parameters
        ----------
        todo_id : str
            The todoID UUID.
        user_id : str
            The owning userID UUID (ownership check).

        Returns
        -------
        dict | None
            The current row dict, or None if not found / deleted.
        """
        sql = """
            SELECT t.todoID, t.title, t.content, t.due, t.list_type,
                   t.list_name, t.position, t.completed, t.added
            FROM todo t
            WHERE t.todoID = %s
              AND t.userID = %s
              AND t.id = (
                  SELECT MAX(t2.id) FROM todo t2 WHERE t2.todoID = t.todoID
              )
              AND t.title IS NOT NULL
        """
        return db_manager.execute_one(sql, (todo_id, user_id))

    @staticmethod
    def search(user_id: str, query: str) -> list[dict]:
        """
        Full-text search across title and content for *user_id*.

        Uses LIKE pattern matching against title (primary) and content
        (secondary).  Results are ordered by due date descending so the
        most recent items appear first.

        Parameters
        ----------
        user_id : str
            The userID UUID.
        query : str
            Search string; % wildcards are added automatically.

        Returns
        -------
        list[dict]
            Each dict: todoID, title, content, due, list_type, list_name,
            position, completed, added.
        """
        pattern = f'%{query}%'
        sql = """
            SELECT t.todoID, t.title, t.content, t.due, t.list_type,
                   t.list_name, t.position, t.completed, t.added
            FROM todo t
            WHERE t.userID = %s
              AND t.id = (
                  SELECT MAX(t2.id) FROM todo t2 WHERE t2.todoID = t.todoID
              )
              AND t.title IS NOT NULL
              AND (t.title LIKE %s OR t.content LIKE %s)
            ORDER BY t.due DESC, t.position, t.created
        """
        return db_manager.execute_query(sql, (user_id, pattern, pattern))

    @staticmethod
    def get_all_lists(user_id: str) -> dict:
        """
        Return all planning and custom list names for *user_id*.

        Planning lists are fixed; custom list names are read from the
        ``user_preference`` table (preference keys: todo_list1_name …
        todo_list4_name).

        Parameters
        ----------
        user_id : str
            The userID UUID.

        Returns
        -------
        dict
            {
              'planning': ['next_week', 'this_month', 'next_month', 'someday_soon'],
              'custom':   ['List 1', 'List 2', ...]   # only named lists
            }
        """
        planning = ['next_week', 'this_month', 'next_month', 'someday_soon']

        # Fetch custom list names from user preferences
        sql = """
            SELECT p.preference, p.value
            FROM user_preference p
            WHERE p.userID = %s
              AND p.preference IN (
                  'todo_list1_name', 'todo_list2_name',
                  'todo_list3_name', 'todo_list4_name'
              )
              AND p.id = (
                  SELECT MAX(p2.id) FROM user_preference p2
                  WHERE p2.userID = p.userID AND p2.preference = p.preference
              )
        """
        rows = db_manager.execute_query(sql, (user_id,))
        prefs = {r['preference']: r['value'] for r in rows}

        custom = []
        for i in range(1, 5):
            name = prefs.get(f'todo_list{i}_name', '').strip()
            if name:
                custom.append(name)

        return {'planning': planning, 'custom': custom}

    # ------------------------------------------------------------------
    # Write helpers (insert-only pattern)
    # ------------------------------------------------------------------

    @staticmethod
    def create(
        user_id: str,
        title: str,
        due: date = None,
        list_type: str = 'daily',
        list_name: str = None,
        position: int = 0,
        content: str = None,
    ) -> str:
        """
        Insert a new todo item and return its todoID.

        A fresh UUID is generated for each new todo so it can be tracked
        through subsequent inserts (update/delete use the same todoID).

        Parameters
        ----------
        user_id : str
            The owning userID UUID.
        title : str
            Required todo title text.
        due : date, optional
            Due date (required for daily list_type).
        list_type : str
            One of 'daily', 'custom', 'planning'.
        list_name : str, optional
            Required for custom/planning list types.
        position : int
            Sort order within the list.
        content : str, optional
            Optional Markdown body text.

        Returns
        -------
        str
            The new todoID UUID string.
        """
        todo_id = str(uuid.uuid4())
        today = date.today()
        sql = """
            INSERT INTO todo (todoID, userID, title, content, due, list_type,
                              list_name, position, added, created, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """
        db_manager.execute_insert(sql, (
            todo_id, user_id, title, content, due, list_type,
            list_name, position, due or today, user_id,
        ))
        return todo_id

    @staticmethod
    def update(
        todo_id: str,
        user_id: str,
        title: str = None,
        content: str = None,
        due: date = None,
        position: int = None,
        completed: datetime = None,
    ) -> None:
        """
        Update a todo by inserting a new record with modified fields.

        Fetches the current state first, then inserts a new row with the
        same todoID applying any supplied override values.  Fields not
        passed remain unchanged from the current record.

        Parameters
        ----------
        todo_id : str
            The todoID to update.
        user_id : str
            Ownership verification; new record is created_by this user.
        title, content, due, position, completed
            Any subset of fields to change.  Pass None to keep existing.
        """
        current = TodoModel.get_todo_by_id(todo_id, user_id)
        if current is None:
            return

        new_title     = title     if title     is not None else current['title']
        new_content   = content   if content   is not None else current['content']
        new_due       = due       if due       is not None else current['due']
        new_position  = position  if position  is not None else current['position']
        new_completed = completed if completed is not None else current['completed']

        sql = """
            INSERT INTO todo (todoID, userID, title, content, due, list_type,
                              list_name, position, completed, added, created, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """
        db_manager.execute_insert(sql, (
            todo_id, user_id,
            new_title, new_content, new_due,
            current['list_type'], current['list_name'],
            new_position, new_completed,
            current['added'],
            user_id,
        ))

    @staticmethod
    def delete(todo_id: str, user_id: str) -> None:
        """
        Soft-delete a todo by inserting a new record with title=NULL.

        Parameters
        ----------
        todo_id : str
            The todoID to delete.
        user_id : str
            Ownership verification.
        """
        current = TodoModel.get_todo_by_id(todo_id, user_id)
        if current is None:
            return

        sql = """
            INSERT INTO todo (todoID, userID, title, content, due, list_type,
                              list_name, position, completed, added, created, created_by)
            VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """
        db_manager.execute_insert(sql, (
            todo_id, user_id,
            current['content'], current['due'],
            current['list_type'], current['list_name'],
            current['position'], current['completed'],
            current['added'],
            user_id,
        ))

    @staticmethod
    def toggle_complete(todo_id: str, user_id: str) -> None:
        """
        Toggle completion status of a todo using the insert-only pattern.

        If the current record has ``completed=NULL``, the new record sets
        ``completed=NOW()``.  If it is already set, the new record clears it
        to ``NULL``.

        Parameters
        ----------
        todo_id : str
            The todoID to toggle.
        user_id : str
            Ownership verification.
        """
        current = TodoModel.get_todo_by_id(todo_id, user_id)
        if current is None:
            return

        if current['completed'] is None:
            new_completed = datetime.now()
        else:
            new_completed = None

        sql = """
            INSERT INTO todo (todoID, userID, title, content, due, list_type,
                              list_name, position, completed, added, created, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """
        db_manager.execute_insert(sql, (
            todo_id, user_id,
            current['title'], current['content'],
            current['due'], current['list_type'], current['list_name'],
            current['position'], new_completed,
            current['added'],
            user_id,
        ))

    @staticmethod
    def move(
        todo_id: str,
        user_id: str,
        new_due: date = None,
        new_list_type: str = None,
        new_list_name: str = None,
    ) -> None:
        """
        Move a todo to a different date or list by inserting a new record.

        Parameters
        ----------
        todo_id : str
            The todoID to move.
        user_id : str
            Ownership verification.
        new_due : date, optional
            New due date.  Clears to None if not provided (non-daily lists).
        new_list_type : str, optional
            New list type ('daily', 'custom', 'planning').
        new_list_name : str, optional
            New list name (for custom/planning).
        """
        current = TodoModel.get_todo_by_id(todo_id, user_id)
        if current is None:
            return

        move_due       = new_due       if new_due       is not None else current['due']
        move_list_type = new_list_type if new_list_type is not None else current['list_type']
        move_list_name = new_list_name if new_list_name is not None else current['list_name']

        sql = """
            INSERT INTO todo (todoID, userID, title, content, due, list_type,
                              list_name, position, completed, added, created, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """
        db_manager.execute_insert(sql, (
            todo_id, user_id,
            current['title'], current['content'],
            move_due, move_list_type, move_list_name,
            current['position'], current['completed'],
            current['added'],
            user_id,
        ))

    @staticmethod
    def reorder(user_id: str, todo_ids: list[str], positions: list[int]) -> None:
        """
        Update the sort position for multiple todos simultaneously.

        Each pair ``(todo_ids[i], positions[i])`` represents one item to
        reposition.  A new record is inserted for each, preserving all
        other fields.  Pairs with a missing current record are silently
        skipped.

        Parameters
        ----------
        user_id : str
            The owning userID UUID.
        todo_ids : list[str]
            Ordered list of todoID UUIDs.
        positions : list[int]
            Corresponding new position values.
        """
        for todo_id, position in zip(todo_ids, positions):
            current = TodoModel.get_todo_by_id(todo_id, user_id)
            if current is None:
                continue
            sql = """
                INSERT INTO todo (todoID, userID, title, content, due, list_type,
                                  list_name, position, completed, added, created, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """
            db_manager.execute_insert(sql, (
                todo_id, user_id,
                current['title'], current['content'],
                current['due'], current['list_type'], current['list_name'],
                position, current['completed'],
                current['added'],
                user_id,
            ))

    # ------------------------------------------------------------------
    # Push-forward logic
    # ------------------------------------------------------------------

    @staticmethod
    def push_forward_check(user_id: str, today: date) -> bool:
        """
        Return True if the daily push-forward has already run for *today*.

        Checks whether any ``todo_pushedForward`` record linked to this
        user's todos was created on *today*.  A True result means the
        push-forward should be skipped to avoid duplicates.

        Parameters
        ----------
        user_id : str
            The userID UUID.
        today : date
            The current calendar date.

        Returns
        -------
        bool
        """
        sql = """
            SELECT COUNT(*) AS cnt
            FROM todo_pushedForward pf
            JOIN todo t ON t.todoID = pf.todoID
            WHERE t.userID = %s
              AND DATE(pf.created) = %s
        """
        result = db_manager.execute_one(sql, (user_id, today))
        return (result['cnt'] > 0) if result else False

    @staticmethod
    def push_forward(user_id: str, today: date) -> int:
        """
        Move all incomplete daily todo items from yesterday to today.

        For each incomplete item from yesterday that has not already been
        pushed today:

        1. Insert a new ``todo`` row with ``due=today`` and the same
           todoID (preserving the ``added`` original-due-date).
        2. Insert a ``todo_pushedForward`` row to record the move.

        The check in step 1 (``todo_pushedForward`` lookup) makes the
        operation safe to call multiple times concurrently — each call
        may insert duplicate push records, but the todo state will be
        correct because the highest-id row wins.

        Parameters
        ----------
        user_id : str
            The userID UUID.
        today : date
            The current calendar date (push target).

        Returns
        -------
        int
            Count of items moved.
        """
        yesterday = today - timedelta(days=1)

        # Fetch all incomplete daily items from yesterday
        sql = """
            SELECT t.todoID, t.title, t.content, t.list_type, t.list_name,
                   t.position, t.added
            FROM todo t
            WHERE t.userID = %s
              AND t.due = %s
              AND t.list_type = 'daily'
              AND t.id = (
                  SELECT MAX(t2.id) FROM todo t2 WHERE t2.todoID = t.todoID
              )
              AND t.title IS NOT NULL
              AND t.completed IS NULL
        """
        todos = db_manager.execute_query(sql, (user_id, yesterday))

        count = 0
        for todo in todos:
            # Count how many times this todo has been pushed before today
            prior_sql = """
                SELECT COUNT(*) AS cnt FROM todo_pushedForward
                WHERE todoID = %s AND DATE(created) < %s
            """
            prior_result = db_manager.execute_one(prior_sql, (todo['todoID'], today))
            prior_count = prior_result['cnt'] if prior_result else 0

            # Skip if already pushed today
            check_sql = """
                SELECT id FROM todo_pushedForward
                WHERE todoID = %s AND DATE(created) = %s
            """
            already = db_manager.execute_one(check_sql, (todo['todoID'], today))
            if already:
                continue

            # Determine target list based on prior push count
            if prior_count == 0:
                # First push: keep in daily list, move to today
                target_due = today
                target_type = 'daily'
                target_name = None
            else:
                # Subsequent push: move to Someday planning list
                target_due = None
                target_type = 'planning'
                target_name = 'someday_soon'

            # Insert new todo record
            insert_sql = """
                INSERT INTO todo (todoID, userID, title, content, due, list_type,
                                  list_name, position, added, created, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """
            db_manager.execute_insert(insert_sql, (
                todo['todoID'], user_id,
                todo['title'], todo['content'],
                target_due, target_type, target_name,
                todo['position'],
                todo['added'] or yesterday,
                user_id,
            ))

            # Record the push in todo_pushedForward
            pf_sql = """
                INSERT INTO todo_pushedForward (todoID, created, created_by)
                VALUES (%s, NOW(), %s)
            """
            db_manager.execute_insert(pf_sql, (todo['todoID'], user_id))

            count += 1

        return count
