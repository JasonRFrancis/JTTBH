"""
Topic Model
===========
Master list of tags shared across features (study, quote, ...). Managed by
admins on the /admin/topics page; other features read it read-only to
prefill their own tag inputs.

Flat, admin-managed reference list — direct UPDATE/DELETE, no insert-only
versioning (same shape as fitness_exercise / svg).
"""

from app.services.database import db_manager


class TopicModel:

    @staticmethod
    def get_all() -> list[dict]:
        return db_manager.execute_query(
            "SELECT id, name FROM topic ORDER BY name", ())

    @staticmethod
    def create(name: str, user_id: str) -> int | None:
        """Returns the new topic's id, or None if that name already exists."""
        if db_manager.execute_one("SELECT id FROM topic WHERE name = %s", (name,)):
            return None
        return db_manager.execute_insert(
            "INSERT INTO topic (name, created, created_by) VALUES (%s, NOW(), %s)",
            (name, user_id),
        )

    @staticmethod
    def delete(topic_id: int) -> None:
        db_manager.execute_update("DELETE FROM topic WHERE id=%s", (topic_id,))
