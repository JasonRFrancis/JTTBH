from datetime import date as date_cls
import uuid

from app.services.database import db_manager


class StudyModel:

    # ------------------------------------------------------------------
    # Collections
    # ------------------------------------------------------------------

    @staticmethod
    def get_all_collections() -> list[dict]:
        return db_manager.execute_query("""
            SELECT sc.collectionID, sc.userID, sc.name, sc.description, sc.mode,
                   u.username AS owner_username,
                   (SELECT COUNT(*) FROM study_source ss
                    WHERE ss.collectionID = sc.collectionID
                      AND ss.id = (SELECT MAX(ss2.id) FROM study_source ss2 WHERE ss2.sourceID = ss.sourceID)
                      AND ss.title IS NOT NULL
                   ) AS source_count
            FROM study_collection sc
            LEFT JOIN `user` u ON u.userID = sc.userID
            WHERE sc.id = (SELECT MAX(sc2.id) FROM study_collection sc2 WHERE sc2.collectionID = sc.collectionID)
              AND sc.name IS NOT NULL
            ORDER BY sc.name
        """, ())

    @staticmethod
    def get_collection(collection_id: str) -> dict | None:
        return db_manager.execute_one("""
            SELECT sc.collectionID, sc.userID, sc.name, sc.description, sc.mode,
                   u.username AS owner_username
            FROM study_collection sc
            LEFT JOIN `user` u ON u.userID = sc.userID
            WHERE sc.collectionID = %s
              AND sc.id = (SELECT MAX(sc2.id) FROM study_collection sc2 WHERE sc2.collectionID = sc.collectionID)
              AND sc.name IS NOT NULL
        """, (collection_id,))

    @staticmethod
    def create_collection(user_id: str, name: str, description: str, mode: str) -> str:
        collection_id = str(uuid.uuid4())
        db_manager.execute_insert(
            "INSERT INTO study_collection (collectionID, userID, name, description, mode, created, created_by) VALUES (%s,%s,%s,%s,%s,NOW(),%s)",
            (collection_id, user_id, name, description or None, mode, user_id),
        )
        return collection_id

    @staticmethod
    def update_collection(collection_id: str, user_id: str, name: str, description: str, mode: str):
        db_manager.execute_insert(
            "INSERT INTO study_collection (collectionID, userID, name, description, mode, created, created_by) VALUES (%s,%s,%s,%s,%s,NOW(),%s)",
            (collection_id, user_id, name, description or None, mode, user_id),
        )

    @staticmethod
    def delete_collection(collection_id: str, user_id: str):
        db_manager.execute_insert(
            "INSERT INTO study_collection (collectionID, userID, name, description, mode, created, created_by) VALUES (%s,%s,NULL,NULL,'rate',NOW(),%s)",
            (collection_id, user_id, user_id),
        )

    # ------------------------------------------------------------------
    # Sources
    # ------------------------------------------------------------------

    @staticmethod
    def get_sources(collection_id: str) -> list[dict]:
        return db_manager.execute_query("""
            SELECT ss.sourceID, ss.collectionID, ss.userID, ss.category, ss.title,
                   ss.subtitle, ss.author, ss.url, ss.audio_url, ss.audio_length,
                   ss.order_by, ss.scheduled_date
            FROM study_source ss
            WHERE ss.collectionID = %s
              AND ss.id = (SELECT MAX(ss2.id) FROM study_source ss2 WHERE ss2.sourceID = ss.sourceID)
              AND ss.title IS NOT NULL
            ORDER BY ss.order_by, ss.id
        """, (collection_id,))

    @staticmethod
    def get_source(source_id: str) -> dict | None:
        return db_manager.execute_one("""
            SELECT ss.sourceID, ss.collectionID, ss.userID, ss.category, ss.title,
                   ss.subtitle, ss.author, ss.url, ss.audio_url, ss.audio_length,
                   ss.order_by, ss.scheduled_date
            FROM study_source ss
            WHERE ss.sourceID = %s
              AND ss.id = (SELECT MAX(ss2.id) FROM study_source ss2 WHERE ss2.sourceID = ss.sourceID)
              AND ss.title IS NOT NULL
        """, (source_id,))

    @staticmethod
    def create_source(user_id: str, collection_id: str, category: str, title: str,
                      subtitle: str, author: str, url: str, audio_url: str,
                      audio_length: str, order_by: int, scheduled_date) -> str:
        source_id = str(uuid.uuid4())
        db_manager.execute_insert(
            """INSERT INTO study_source
               (sourceID, collectionID, userID, category, title, subtitle, author,
                url, audio_url, audio_length, order_by, scheduled_date, created, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s)""",
            (source_id, collection_id, user_id, category or None, title,
             subtitle or None, author or None, url or None, audio_url or None,
             audio_length or None, order_by, scheduled_date, user_id),
        )
        return source_id

    @staticmethod
    def update_source(source_id: str, collection_id: str, user_id: str, category: str,
                      title: str, subtitle: str, author: str, url: str, audio_url: str,
                      audio_length: str, order_by: int, scheduled_date):
        db_manager.execute_insert(
            """INSERT INTO study_source
               (sourceID, collectionID, userID, category, title, subtitle, author,
                url, audio_url, audio_length, order_by, scheduled_date, created, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s)""",
            (source_id, collection_id, user_id, category or None, title,
             subtitle or None, author or None, url or None, audio_url or None,
             audio_length or None, order_by, scheduled_date, user_id),
        )

    @staticmethod
    def delete_source(source_id: str, collection_id: str, user_id: str):
        db_manager.execute_insert(
            "INSERT INTO study_source (sourceID, collectionID, userID, category, title, order_by, created, created_by) VALUES (%s,%s,%s,NULL,NULL,0,NOW(),%s)",
            (source_id, collection_id, user_id, user_id),
        )

    # ------------------------------------------------------------------
    # Subscriptions
    # ------------------------------------------------------------------

    @staticmethod
    def get_user_subscriptions(user_id: str) -> list[dict]:
        return db_manager.execute_query("""
            SELECT sub.subscriptionID, sub.userID, sub.collectionID,
                   sub.per_day, sub.start_date,
                   sc.name AS collection_name, sc.description AS collection_description,
                   sc.mode
            FROM study_subscription sub
            JOIN study_collection sc ON sc.collectionID = sub.collectionID
              AND sc.id = (SELECT MAX(sc2.id) FROM study_collection sc2 WHERE sc2.collectionID = sc.collectionID)
              AND sc.name IS NOT NULL
            WHERE sub.userID = %s
            ORDER BY sc.name
        """, (user_id,))

    @staticmethod
    def get_subscription(user_id: str, collection_id: str) -> dict | None:
        return db_manager.execute_one(
            "SELECT * FROM study_subscription WHERE userID = %s AND collectionID = %s",
            (user_id, collection_id),
        )

    @staticmethod
    def get_subscription_by_id(subscription_id: str) -> dict | None:
        return db_manager.execute_one(
            "SELECT * FROM study_subscription WHERE subscriptionID = %s",
            (subscription_id,),
        )

    @staticmethod
    def create_subscription(user_id: str, collection_id: str, per_day: int, start_date) -> str:
        subscription_id = str(uuid.uuid4())
        db_manager.execute_insert(
            "INSERT INTO study_subscription (subscriptionID, userID, collectionID, per_day, start_date, created, created_by) VALUES (%s,%s,%s,%s,%s,NOW(),%s)",
            (subscription_id, user_id, collection_id, per_day, start_date, user_id),
        )
        return subscription_id

    @staticmethod
    def update_subscription(subscription_id: str, per_day: int, start_date):
        db_manager.execute_update(
            "UPDATE study_subscription SET per_day=%s, start_date=%s WHERE subscriptionID=%s",
            (per_day, start_date, subscription_id),
        )

    @staticmethod
    def delete_subscription(subscription_id: str):
        db_manager.execute_update(
            "DELETE FROM study_subscription WHERE subscriptionID=%s",
            (subscription_id,),
        )

    # ------------------------------------------------------------------
    # Daily calculation
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Completions
    # ------------------------------------------------------------------

    @staticmethod
    def get_completions_for_date(user_id: str, target_date) -> set[str]:
        rows = db_manager.execute_query(
            "SELECT sourceID FROM study_completion WHERE userID=%s AND completed_date=%s",
            (user_id, target_date),
        )
        return {r['sourceID'] for r in rows}

    @staticmethod
    def toggle_completion(user_id: str, source_id: str, completed_date):
        existing = db_manager.execute_one(
            "SELECT id FROM study_completion WHERE userID=%s AND sourceID=%s AND completed_date=%s",
            (user_id, source_id, completed_date),
        )
        if existing:
            db_manager.execute_update(
                "DELETE FROM study_completion WHERE userID=%s AND sourceID=%s AND completed_date=%s",
                (user_id, source_id, completed_date),
            )
        else:
            db_manager.execute_insert(
                "INSERT INTO study_completion (completionID, userID, sourceID, completed_date, created, created_by) VALUES (%s,%s,%s,%s,NOW(),%s)",
                (str(uuid.uuid4()), user_id, source_id, completed_date, user_id),
            )

    # ------------------------------------------------------------------
    # Daily calculation
    # ------------------------------------------------------------------

    @staticmethod
    def sources_for_date(subscription: dict, sources: list[dict], target_date) -> list[dict]:
        mode = subscription.get('mode')
        if mode == 'calendar':
            return [s for s in sources if s.get('scheduled_date') == target_date]
        # rate mode
        start = subscription.get('start_date')
        if start is None or not sources:
            return []
        if isinstance(start, str):
            start = date_cls.fromisoformat(start)
        days = (target_date - start).days
        if days < 0:
            return []
        per_day = subscription.get('per_day', 1)
        start_idx = (days * per_day) % len(sources)
        return [sources[(start_idx + i) % len(sources)] for i in range(per_day)]
