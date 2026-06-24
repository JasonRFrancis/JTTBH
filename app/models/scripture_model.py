"""
Scripture Model
===============
Database interactions for the scripture memorization feature.

``scripture`` uses the insert-only pattern; ``reference IS NULL`` = soft-deleted.
``scripture_review`` uses direct UPDATE because it holds mutable SR state.

Public API
----------
    ScriptureModel.get_all(user_id)                          -> list[dict]
    ScriptureModel.get_one(user_id, scripture_id)            -> dict | None
    ScriptureModel.create(user_id, reference, text,
                          summary, modes)                    -> str
    ScriptureModel.update(user_id, scripture_id, reference,
                          text, summary, modes)              -> None
    ScriptureModel.delete(user_id, scripture_id)             -> None
    ScriptureModel.get_due_reviews(user_id)                  -> list[dict]
    ScriptureModel.get_review_states(user_id)                -> list[dict]
    ScriptureModel.grade_review(user_id, scripture_id,
                                mode, quality)               -> None
"""

import uuid
from datetime import date, timedelta

from app.services.database import db_manager

_MODES = ('reference', 'familiar', 'verbatim')


def _sm2(ease_factor: float, interval: int, repetitions: int,
         quality: int) -> tuple[float, int, int]:
    """SM-2 algorithm. quality: 0=again, 3=hard, 4=good, 5=easy."""
    if quality < 3:
        repetitions, interval = 0, 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ease_factor)
        repetitions += 1
    ease_factor = ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    ease_factor = max(1.3, ease_factor)
    return ease_factor, interval, repetitions


class ScriptureModel:

    @staticmethod
    def get_all(user_id: str) -> list[dict]:
        return db_manager.execute_query("""
            SELECT s.scriptureID, s.reference, s.text, s.summary, s.created
            FROM scripture s
            WHERE s.userID = %s
              AND s.id = (SELECT MAX(s2.id) FROM scripture s2
                          WHERE s2.scriptureID = s.scriptureID)
              AND s.reference IS NOT NULL
            ORDER BY s.id DESC
        """, (user_id,))

    @staticmethod
    def get_one(user_id: str, scripture_id: str) -> dict | None:
        return db_manager.execute_one("""
            SELECT s.scriptureID, s.reference, s.text, s.summary, s.created
            FROM scripture s
            WHERE s.userID = %s
              AND s.scriptureID = %s
              AND s.id = (SELECT MAX(s2.id) FROM scripture s2
                          WHERE s2.scriptureID = s.scriptureID)
              AND s.reference IS NOT NULL
        """, (user_id, scripture_id))

    @staticmethod
    def create(user_id: str, reference: str, text: str, summary: str,
               modes: list[str]) -> str:
        scripture_id = str(uuid.uuid4())
        db_manager.execute_insert("""
            INSERT INTO scripture
                (scriptureID, userID, reference, text, summary, created, created_by)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s)
        """, (scripture_id, user_id, reference, text or None,
              summary or None, user_id))

        today = date.today().isoformat()
        for mode in modes:
            if mode in _MODES:
                db_manager.execute_insert("""
                    INSERT INTO scripture_review
                        (scriptureID, userID, mode, ease_factor, interval_days,
                         repetitions, next_review)
                    VALUES (%s, %s, %s, 2.50, 1, 0, %s)
                    ON DUPLICATE KEY UPDATE next_review = next_review
                """, (scripture_id, user_id, mode, today))

        return scripture_id

    @staticmethod
    def update(user_id: str, scripture_id: str, reference: str, text: str,
               summary: str, modes: list[str]) -> None:
        db_manager.execute_insert("""
            INSERT INTO scripture
                (scriptureID, userID, reference, text, summary, created, created_by)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s)
        """, (scripture_id, user_id, reference, text or None,
              summary or None, user_id))

        today = date.today().isoformat()
        for mode in _MODES:
            if mode in modes:
                # Insert review row if it doesn't already exist for this mode
                db_manager.execute_insert("""
                    INSERT INTO scripture_review
                        (scriptureID, userID, mode, ease_factor, interval_days,
                         repetitions, next_review)
                    VALUES (%s, %s, %s, 2.50, 1, 0, %s)
                    ON DUPLICATE KEY UPDATE next_review = next_review
                """, (scripture_id, user_id, mode, today))
            else:
                # Remove review row if mode was deselected
                db_manager.execute_update("""
                    DELETE FROM scripture_review
                    WHERE scriptureID = %s AND userID = %s AND mode = %s
                """, (scripture_id, user_id, mode))

    @staticmethod
    def delete(user_id: str, scripture_id: str) -> None:
        db_manager.execute_insert("""
            INSERT INTO scripture
                (scriptureID, userID, reference, created, created_by)
            VALUES (%s, %s, NULL, NOW(), %s)
        """, (scripture_id, user_id, user_id))

    @staticmethod
    def get_due_reviews(user_id: str) -> list[dict]:
        return db_manager.execute_query("""
            SELECT s.scriptureID, s.reference, s.text, s.summary,
                   r.mode, r.ease_factor, r.interval_days, r.repetitions,
                   r.next_review, r.last_reviewed
            FROM scripture_review r
            JOIN scripture s
              ON s.scriptureID = r.scriptureID
             AND s.id = (SELECT MAX(s2.id) FROM scripture s2
                         WHERE s2.scriptureID = s.scriptureID)
             AND s.reference IS NOT NULL
            WHERE r.userID = %s
              AND r.next_review <= CURDATE()
            ORDER BY r.next_review ASC, r.mode ASC
        """, (user_id,))

    @staticmethod
    def get_review_states(user_id: str) -> list[dict]:
        return db_manager.execute_query("""
            SELECT r.scriptureID, r.mode, r.ease_factor, r.interval_days,
                   r.repetitions, r.next_review, r.last_reviewed
            FROM scripture_review r
            WHERE r.userID = %s
        """, (user_id,))

    @staticmethod
    def get_due_count(user_id: str) -> int:
        row = db_manager.execute_one("""
            SELECT COUNT(*) AS cnt
            FROM scripture_review r
            JOIN scripture s
              ON s.scriptureID = r.scriptureID
             AND s.id = (SELECT MAX(s2.id) FROM scripture s2
                         WHERE s2.scriptureID = s.scriptureID)
             AND s.reference IS NOT NULL
            WHERE r.userID = %s
              AND r.next_review <= CURDATE()
        """, (user_id,))
        return row['cnt'] if row else 0

    @staticmethod
    def grade_review(user_id: str, scripture_id: str, mode: str,
                     quality: int) -> None:
        row = db_manager.execute_one("""
            SELECT ease_factor, interval_days, repetitions
            FROM scripture_review
            WHERE scriptureID = %s AND userID = %s AND mode = %s
        """, (scripture_id, user_id, mode))
        if not row:
            return

        ef, interval, reps = _sm2(
            float(row['ease_factor']),
            int(row['interval_days']),
            int(row['repetitions']),
            quality,
        )
        next_review = (date.today() + timedelta(days=interval)).isoformat()

        db_manager.execute_update("""
            UPDATE scripture_review
            SET ease_factor   = %s,
                interval_days = %s,
                repetitions   = %s,
                next_review   = %s,
                last_reviewed = NOW()
            WHERE scriptureID = %s AND userID = %s AND mode = %s
        """, (round(ef, 2), interval, reps, next_review,
              scripture_id, user_id, mode))
