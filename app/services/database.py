"""
JTTBH Database Service
=======================
Thin wrapper around PyMySQL that provides four clean primitives for executing
SQL without an ORM:

    db_manager.execute_query(sql, params)   -> list[dict]
    db_manager.execute_one(sql, params)     -> dict | None
    db_manager.execute_insert(sql, params)  -> int  (lastrowid)
    db_manager.execute_update(sql, params)  -> int  (rowcount)

A fresh connection is opened for every call and closed immediately after.
This is safe for low-to-medium traffic; replace with a connection pool
(e.g. DBUtils PooledDB) if higher throughput is required.

Configuration is read from environment variables at import time and cached
in the singleton ``db_manager``.
"""

import os
import sys
import traceback

import pymysql
import pymysql.cursors


# ---------------------------------------------------------------------------
# DatabaseManager
# ---------------------------------------------------------------------------

class DatabaseManager:
    """
    Manages MySQL connections and query execution using PyMySQL.

    All public methods open a fresh connection, execute the statement, commit
    if necessary, and close the connection.  Errors are printed to stderr and
    re-raised so the caller can decide how to handle them.
    """

    def __init__(self):
        """Read connection parameters from environment variables.

        Note: env vars are read on each _connect() call (not cached) so that
        values loaded from .env by the app factory are always picked up.
        """

    def _get_config(self):
        """Read current connection config from environment."""
        return {
            'host':     os.environ.get('MYSQL_HOST',     'localhost'),
            'port':     int(os.environ.get('MYSQL_PORT', 3306)),
            'user':     os.environ.get('MYSQL_USER',     'jttbh'),
            'password': os.environ.get('MYSQL_PASSWORD', 'jttbh'),
            # Support both MYSQL_DB and MYSQL_DATABASE
            'db':       os.environ.get('MYSQL_DB') or os.environ.get('MYSQL_DATABASE', 'jttbh'),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _connect(self) -> pymysql.Connection:
        """
        Open and return a new database connection.

        Uses ``DictCursor`` so every row is returned as a plain Python dict
        instead of a tuple, which makes result handling much easier.
        Reads config fresh each call so .env values loaded by the app
        factory are always used.
        """
        cfg = self._get_config()
        return pymysql.connect(
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['db'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )

    def _log_error(self, sql: str, params, exc: Exception) -> None:
        """Write a formatted error message to stderr."""
        print(
            f'[DatabaseManager] Error executing SQL:\n'
            f'  SQL   : {sql!r}\n'
            f'  Params: {params!r}\n'
            f'  Error : {exc}\n'
            f'{traceback.format_exc()}',
            file=sys.stderr,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute_query(self, sql: str, params=None) -> list[dict]:
        """
        Execute a SELECT statement and return all matching rows.

        Parameters
        ----------
        sql : str
            The SQL query.  Use ``%s`` placeholders for parameters.
        params : tuple | list | None
            Values to substitute into the query placeholders.

        Returns
        -------
        list[dict]
            A (possibly empty) list of row dictionaries.

        Raises
        ------
        pymysql.Error
            On any database error.
        """
        conn = None
        try:
            conn = self._connect()
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()
        except pymysql.Error as exc:
            self._log_error(sql, params, exc)
            raise
        finally:
            if conn:
                conn.close()

    def execute_one(self, sql: str, params=None) -> dict | None:
        """
        Execute a SELECT statement and return the first row, or ``None``.

        Parameters
        ----------
        sql : str
            The SQL query.  Use ``%s`` placeholders for parameters.
        params : tuple | list | None
            Values to substitute into the query placeholders.

        Returns
        -------
        dict | None
            The first result row as a dict, or ``None`` if no rows matched.

        Raises
        ------
        pymysql.Error
            On any database error.
        """
        conn = None
        try:
            conn = self._connect()
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchone()
        except pymysql.Error as exc:
            self._log_error(sql, params, exc)
            raise
        finally:
            if conn:
                conn.close()

    def execute_insert(self, sql: str, params=None) -> int:
        """
        Execute an INSERT statement and return the auto-increment ID.

        Parameters
        ----------
        sql : str
            The INSERT statement.  Use ``%s`` placeholders for parameters.
        params : tuple | list | None
            Values to substitute into the query placeholders.

        Returns
        -------
        int
            ``cursor.lastrowid`` – the primary key of the newly inserted row.
            Returns 0 if the table has no auto-increment column.

        Raises
        ------
        pymysql.Error
            On any database error (the transaction is rolled back).
        """
        conn = None
        try:
            conn = self._connect()
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
        except pymysql.Error as exc:
            if conn:
                conn.rollback()
            self._log_error(sql, params, exc)
            raise
        finally:
            if conn:
                conn.close()

    def execute_update(self, sql: str, params=None) -> int:
        """
        Execute an UPDATE or DELETE statement and return the affected row count.

        Parameters
        ----------
        sql : str
            The UPDATE or DELETE statement.  Use ``%s`` placeholders.
        params : tuple | list | None
            Values to substitute into the query placeholders.

        Returns
        -------
        int
            ``cursor.rowcount`` – the number of rows affected.

        Raises
        ------
        pymysql.Error
            On any database error (the transaction is rolled back).
        """
        conn = None
        try:
            conn = self._connect()
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount
        except pymysql.Error as exc:
            if conn:
                conn.rollback()
            self._log_error(sql, params, exc)
            raise
        finally:
            if conn:
                conn.close()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

#: Shared DatabaseManager instance.  Import this in all route modules:
#:
#:     from app.services.database import db_manager
db_manager = DatabaseManager()
