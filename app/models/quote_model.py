"""
Quote Model
===========
All database interactions for the quote feature.

Uses the insert-only pattern: to update a record, insert a new row with the
same quoteID but updated field values.  To soft-delete, insert a new row with
body=NULL.  The current state of any quote is always the row with the highest
``id`` for a given ``quoteID``.

Public API
----------
    QuoteModel.get_all(user_id, tag=None)   -> list[dict]
    QuoteModel.get_one(user_id, quote_id)   -> dict | None
    QuoteModel.create(...)                  -> str  (quoteID)
    QuoteModel.update(...)                  -> None
    QuoteModel.delete(quote_id, user_id)    -> None
    QuoteModel.get_all_tags(user_id)        -> list[str]
"""

import uuid

from app.services.database import db_manager


class QuoteModel:

    @staticmethod
    def get_all(user_id: str, tag: str = None) -> list[dict]:
        rows = db_manager.execute_query("""
            SELECT q.quoteID, q.body, q.author, q.title, q.source, q.tags,
                   q.created
            FROM quote q
            WHERE q.userID = %s
              AND q.id = (SELECT MAX(q2.id) FROM quote q2 WHERE q2.quoteID = q.quoteID)
              AND q.body IS NOT NULL
            ORDER BY q.id DESC
        """, (user_id,))
        if tag:
            tag_lower = tag.lower()
            rows = [
                r for r in rows
                if r['tags'] and tag_lower in [t.strip().lower() for t in r['tags'].split(',')]
            ]
        return rows

    @staticmethod
    def get_one(user_id: str, quote_id: str) -> dict | None:
        return db_manager.execute_one("""
            SELECT q.quoteID, q.body, q.author, q.title, q.source, q.tags,
                   q.created
            FROM quote q
            WHERE q.userID = %s
              AND q.quoteID = %s
              AND q.id = (SELECT MAX(q2.id) FROM quote q2 WHERE q2.quoteID = q.quoteID)
              AND q.body IS NOT NULL
        """, (user_id, quote_id))

    @staticmethod
    def create(user_id: str, body: str, author: str, title: str,
               source: str, tags: str) -> str:
        quote_id = str(uuid.uuid4())
        db_manager.execute_insert("""
            INSERT INTO quote (quoteID, userID, body, author, title, source, tags,
                               created, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """, (quote_id, user_id, body, author or None, title or None,
              source or None, tags or None, user_id))
        return quote_id

    @staticmethod
    def update(user_id: str, quote_id: str, body: str, author: str,
               title: str, source: str, tags: str) -> None:
        db_manager.execute_insert("""
            INSERT INTO quote (quoteID, userID, body, author, title, source, tags,
                               created, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """, (quote_id, user_id, body, author or None, title or None,
              source or None, tags or None, user_id))

    @staticmethod
    def delete(user_id: str, quote_id: str) -> None:
        db_manager.execute_insert("""
            INSERT INTO quote (quoteID, userID, body, created, created_by)
            VALUES (%s, %s, NULL, NOW(), %s)
        """, (quote_id, user_id, user_id))

    @staticmethod
    def get_all_tags(user_id: str) -> list[str]:
        rows = db_manager.execute_query("""
            SELECT q.tags
            FROM quote q
            WHERE q.userID = %s
              AND q.id = (SELECT MAX(q2.id) FROM quote q2 WHERE q2.quoteID = q.quoteID)
              AND q.body IS NOT NULL
              AND q.tags IS NOT NULL
        """, (user_id,))
        seen = set()
        for row in rows:
            for tag in row['tags'].split(','):
                t = tag.strip()
                if t:
                    seen.add(t)
        return sorted(seen, key=str.lower)
