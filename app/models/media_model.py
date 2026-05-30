"""
Media Tracker Model
===================
All database operations for media items and their episodes.
media table uses insert-only (title NULL = soft-delete).
media_episode uses direct UPDATE for the `seen` column.
"""

import uuid
from datetime import datetime

from app.services.database import db_manager

_CURRENT_SQL = """
    SELECT m.mediaID, m.title, m.kind, m.creator, m.status,
           m.rating, m.review, m.external_id, m.cover_url,
           m.streaming, m.next_date, m.started, m.finished
    FROM media m
    WHERE m.userID = %s
      AND m.title IS NOT NULL
      AND m.id = (SELECT MAX(m2.id) FROM media m2 WHERE m2.mediaID = m.mediaID)
    ORDER BY m.kind, m.status, m.created DESC
"""

_BY_ID_SQL = """
    SELECT m.mediaID, m.title, m.kind, m.creator, m.status,
           m.rating, m.review, m.external_id, m.cover_url,
           m.streaming, m.next_date, m.started, m.finished
    FROM media m
    WHERE m.userID = %s
      AND m.mediaID = %s
      AND m.title IS NOT NULL
      AND m.id = (SELECT MAX(m2.id) FROM media m2 WHERE m2.mediaID = m.mediaID)
"""


def get_all(user_id: str) -> list[dict]:
    return db_manager.execute_query(_CURRENT_SQL, (user_id,))


def get_one(user_id: str, media_id: str) -> dict | None:
    return db_manager.execute_one(_BY_ID_SQL, (user_id, media_id))


def create(user_id: str, title: str, kind: str, creator: str | None,
           status: str, external_id: str | None = None,
           cover_url: str | None = None, streaming: str | None = None,
           next_date=None, started=None, finished=None) -> str:
    media_id = str(uuid.uuid4())
    db_manager.execute_insert(
        """INSERT INTO media
           (mediaID, userID, title, kind, creator, status, external_id,
            cover_url, streaming, next_date, started, finished, created, created_by)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s)""",
        (media_id, user_id, title, kind, creator, status, external_id,
         cover_url, streaming, next_date, started, finished, user_id),
    )
    return media_id


def _insert_row(media: dict, user_id: str, **overrides):
    """Insert an update row reusing existing field values."""
    fields = {**media, **overrides}
    db_manager.execute_insert(
        """INSERT INTO media
           (mediaID, userID, title, kind, creator, status, rating, review,
            external_id, cover_url, streaming, next_date, started, finished,
            created, created_by)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s)""",
        (fields['mediaID'], user_id, fields.get('title'), fields['kind'],
         fields.get('creator'), fields['status'], fields.get('rating'),
         fields.get('review'), fields.get('external_id'), fields.get('cover_url'),
         fields.get('streaming'), fields.get('next_date'), fields.get('started'),
         fields.get('finished'), user_id),
    )


def update(user_id: str, media: dict, **overrides):
    _insert_row(media, user_id, **overrides)


def soft_delete(user_id: str, media_id: str):
    db_manager.execute_insert(
        """INSERT INTO media (mediaID, userID, title, kind, status, created, created_by)
           VALUES (%s,%s,NULL,'book','dismiss',NOW(),%s)""",
        (media_id, user_id, user_id),
    )


# ---------------------------------------------------------------------------
# Episodes
# ---------------------------------------------------------------------------

def get_episodes(media_id: str) -> list[dict]:
    return db_manager.execute_query(
        """SELECT episodeID, title, season, episode_number, air_date, seen, description, external_id
           FROM media_episode WHERE mediaID = %s
           ORDER BY season, episode_number, air_date""",
        (media_id,),
    )


def upsert_episode(media_id: str, external_id: str, title: str,
                   season: int | None, episode_number: int | None,
                   air_date, description: str | None, user_id: str):
    """Insert or update episode by external_id. Preserves `seen` on update."""
    existing = db_manager.execute_one(
        "SELECT episodeID FROM media_episode WHERE mediaID = %s AND external_id = %s",
        (media_id, external_id),
    )
    if existing:
        db_manager.execute_update(
            """UPDATE media_episode SET title=%s, season=%s, episode_number=%s,
               air_date=%s, description=%s WHERE episodeID=%s""",
            (title, season, episode_number, air_date, description, existing['episodeID']),
        )
    else:
        ep_id = str(uuid.uuid4())
        db_manager.execute_insert(
            """INSERT INTO media_episode
               (episodeID, mediaID, title, season, episode_number, air_date,
                seen, description, external_id, created, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,0,%s,%s,NOW(),%s)""",
            (ep_id, media_id, title, season, episode_number, air_date,
             description, external_id, user_id),
        )


def set_seen(episode_id: str, seen: bool):
    db_manager.execute_update(
        "UPDATE media_episode SET seen=%s WHERE episodeID=%s",
        (1 if seen else 0, episode_id),
    )
