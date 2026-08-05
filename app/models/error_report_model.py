"""
Error Report Model
===================
Unified triage record for system errors (captured automatically on 500s),
user-submitted bug reports, and feature requests.

Flat, direct UPDATE table (like ``svg``/``topic``) — triage state (status,
priority, admin_notes) mutates in place; no insert-only versioning needed.
"""

import uuid

from app.services.database import db_manager

_DEFAULT_PRIORITY = {
    'system_error': 'high',
    'bug_report': 'medium',
    'feature_request': 'low',
}


class ErrorReportModel:

    @staticmethod
    def create(
        type: str,
        title: str,
        *,
        description: str | None = None,
        userID: str | None = None,
        username: str | None = None,
        url: str | None = None,
        http_method: str | None = None,
        http_status: int | None = None,
        stack_trace: str | None = None,
        request_data: str | None = None,
        user_agent: str | None = None,
        ip: str | None = None,
        priority: str | None = None,
        created_by: str | None = None,
    ) -> str:
        """Insert a new report and return its reportID."""
        report_id = str(uuid.uuid4())
        db_manager.execute_insert(
            """
            INSERT INTO error_report (
                reportID, type, priority, title, description,
                userID, username, url, http_method, http_status,
                stack_trace, request_data, user_agent, ip, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                report_id, type, priority or _DEFAULT_PRIORITY[type], title, description,
                userID, username, url, http_method, http_status,
                stack_trace, request_data, user_agent, ip, created_by,
            ),
        )
        return report_id

    @staticmethod
    def get_all(
        *,
        type: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        userID: str | None = None,
    ) -> list[dict]:
        where, params = ['1=1'], []
        if type:
            where.append('type = %s')
            params.append(type)
        if status:
            where.append('status = %s')
            params.append(status)
        if priority:
            where.append('priority = %s')
            params.append(priority)
        if userID:
            where.append('userID = %s')
            params.append(userID)

        return db_manager.execute_query(
            f"""
            SELECT * FROM error_report
            WHERE {' AND '.join(where)}
            ORDER BY FIELD(priority, 'critical', 'high', 'medium', 'low'), created DESC
            """,
            tuple(params),
        )

    @staticmethod
    def get_by_id(report_id: str) -> dict | None:
        return db_manager.execute_one(
            'SELECT * FROM error_report WHERE reportID = %s', (report_id,)
        )

    @staticmethod
    def update(
        report_id: str,
        *,
        status: str | None = None,
        priority: str | None = None,
        admin_notes: str | None = None,
    ) -> None:
        sets, params = [], []
        if status is not None:
            sets.append('status = %s')
            params.append(status)
            if status == 'resolved':
                sets.append('resolved_at = NOW()')
        if priority is not None:
            sets.append('priority = %s')
            params.append(priority)
        if admin_notes is not None:
            sets.append('admin_notes = %s')
            params.append(admin_notes)
        if not sets:
            return
        params.append(report_id)
        db_manager.execute_update(
            f"UPDATE error_report SET {', '.join(sets)} WHERE reportID = %s",
            tuple(params),
        )

    @staticmethod
    def counts() -> list[dict]:
        """Return per-(type, status) counts for the admin triage summary tiles."""
        return db_manager.execute_query(
            'SELECT type, status, COUNT(*) AS n FROM error_report GROUP BY type, status'
        )
