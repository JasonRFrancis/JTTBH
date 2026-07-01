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

    @staticmethod
    def get_distinct_authors(collection_id: str) -> list[str]:
        rows = db_manager.execute_query("""
            SELECT DISTINCT ss.author
            FROM study_source ss
            WHERE ss.collectionID = %s
              AND ss.id = (SELECT MAX(ss2.id) FROM study_source ss2 WHERE ss2.sourceID = ss.sourceID)
              AND ss.title IS NOT NULL
              AND ss.author IS NOT NULL
              AND ss.author != ''
            ORDER BY ss.author
        """, (collection_id,))
        return [r['author'] for r in rows]

    @staticmethod
    def get_distinct_categories(collection_id: str) -> list[str]:
        rows = db_manager.execute_query("""
            SELECT DISTINCT ss.category
            FROM study_source ss
            WHERE ss.collectionID = %s
              AND ss.id = (SELECT MAX(ss2.id) FROM study_source ss2 WHERE ss2.sourceID = ss.sourceID)
              AND ss.title IS NOT NULL
              AND ss.category IS NOT NULL
              AND ss.category != ''
            ORDER BY ss.category
        """, (collection_id,))
        return [r['category'] for r in rows]

    # ------------------------------------------------------------------
    # Subscriptions
    # ------------------------------------------------------------------

    @staticmethod
    def get_user_subscriptions(user_id: str) -> list[dict]:
        return db_manager.execute_query("""
            SELECT sub.subscriptionID, sub.userID, sub.collectionID,
                   sub.name AS subscription_name,
                   sub.per_day, sub.start_date,
                   sub.filter_author, sub.filter_category,
                   sub.filter_has_audio, sub.filter_title,
                   sub.filter_author_text, sub.filter_category_text,
                   sub.filter_subtitle_text,
                   sub.sort_order, sub.limit_count, sub.start_offset,
                   sub.`repeat`, sub.use_personal_schedule,
                   sc.name AS collection_name, sc.description AS collection_description,
                   sc.mode
            FROM study_subscription sub
            JOIN study_collection sc ON sc.collectionID = sub.collectionID
              AND sc.id = (SELECT MAX(sc2.id) FROM study_collection sc2 WHERE sc2.collectionID = sc.collectionID)
              AND sc.name IS NOT NULL
            WHERE sub.userID = %s
            ORDER BY sub.position, COALESCE(sub.name, sc.name)
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
    def create_subscription(user_id: str, collection_id: str, per_day: int,
                            start_date, name: str = None) -> str:
        subscription_id = str(uuid.uuid4())
        db_manager.execute_insert(
            "INSERT INTO study_subscription (subscriptionID, userID, collectionID, name, per_day, start_date, created, created_by) VALUES (%s,%s,%s,%s,%s,%s,NOW(),%s)",
            (subscription_id, user_id, collection_id, name or None, per_day, start_date, user_id),
        )
        return subscription_id

    @staticmethod
    def update_subscription(subscription_id: str, name: str, per_day: int, start_date,
                            filter_author: str, filter_category: str,
                            filter_has_audio: int, filter_title: str,
                            filter_author_text: str, filter_category_text: str,
                            filter_subtitle_text: str,
                            sort_order: str, limit_count, start_offset: int,
                            repeat: int, use_personal_schedule: int):
        db_manager.execute_update(
            """UPDATE study_subscription
               SET name=%s, per_day=%s, start_date=%s,
                   filter_author=%s, filter_category=%s,
                   filter_has_audio=%s, filter_title=%s,
                   filter_author_text=%s, filter_category_text=%s,
                   filter_subtitle_text=%s,
                   sort_order=%s, limit_count=%s, start_offset=%s,
                   `repeat`=%s, use_personal_schedule=%s
               WHERE subscriptionID=%s""",
            (name or None, per_day, start_date,
             filter_author or None, filter_category or None,
             filter_has_audio, filter_title or None,
             filter_author_text or None, filter_category_text or None,
             filter_subtitle_text or None,
             sort_order, limit_count or None, start_offset,
             repeat, use_personal_schedule,
             subscription_id),
        )

    @staticmethod
    def delete_subscription(subscription_id: str):
        db_manager.execute_update(
            "DELETE FROM study_subscription WHERE subscriptionID=%s",
            (subscription_id,),
        )

    # ------------------------------------------------------------------
    # Smart filtering
    # ------------------------------------------------------------------

    @staticmethod
    def get_filtered_sources(subscription: dict, sources: list[dict]) -> list[dict]:
        """Apply smart subscription filters to a source list."""
        result = list(sources)

        filter_author = subscription.get('filter_author')
        if filter_author:
            allowed = {a.strip().lower() for a in filter_author.split(',') if a.strip()}
            result = [s for s in result if s.get('author') and s['author'].lower() in allowed]

        filter_category = subscription.get('filter_category')
        if filter_category:
            allowed = {c.strip().lower() for c in filter_category.split(',') if c.strip()}
            result = [s for s in result if s.get('category') and s['category'].lower() in allowed]

        filter_category_text = subscription.get('filter_category_text')
        if filter_category_text:
            q = filter_category_text.lower()
            result = [s for s in result if q in (s.get('category') or '').lower()]

        filter_subtitle_text = subscription.get('filter_subtitle_text')
        if filter_subtitle_text:
            q = filter_subtitle_text.lower()
            result = [s for s in result if q in (s.get('subtitle') or '').lower()]

        if subscription.get('filter_has_audio'):
            result = [s for s in result if s.get('audio_url')]

        filter_title = subscription.get('filter_title')
        if filter_title:
            q = filter_title.lower()
            result = [s for s in result if q in (s.get('title') or '').lower()]

        filter_author_text = subscription.get('filter_author_text')
        if filter_author_text:
            q = filter_author_text.lower()
            result = [s for s in result if q in (s.get('author') or '').lower()]

        sort_order = subscription.get('sort_order', 'natural')
        if sort_order == 'newest':
            result = sorted(result, key=lambda s: s.get('order_by', 0), reverse=True)
        elif sort_order == 'oldest':
            result = sorted(result, key=lambda s: s.get('order_by', 0))
        # 'natural' keeps the existing ORDER BY order_by, id from get_sources()

        start_offset = subscription.get('start_offset') or 0
        if start_offset > 0:
            result = result[start_offset:]

        limit_count = subscription.get('limit_count')
        if limit_count:
            result = result[:limit_count]

        return result

    # ------------------------------------------------------------------
    # Completions
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_streak(user_id: str, today) -> int:
        """Consecutive days ending today (or yesterday) with at least one completion."""
        from datetime import timedelta
        rows = db_manager.execute_query(
            "SELECT DISTINCT completed_date FROM study_completion WHERE userID=%s ORDER BY completed_date DESC",
            (user_id,),
        )
        if not rows:
            return 0
        dates = {r['completed_date'] for r in rows}
        check = today if today in dates else today - timedelta(days=1)
        streak = 0
        while check in dates:
            streak += 1
            check -= timedelta(days=1)
        return streak

    @staticmethod
    def get_completions_for_date(user_id: str, target_date) -> set[str]:
        rows = db_manager.execute_query(
            "SELECT sourceID FROM study_completion WHERE userID=%s AND completed_date=%s",
            (user_id, target_date),
        )
        return {r['sourceID'] for r in rows}

    @staticmethod
    def toggle_completion(user_id: str, source_id: str, completed_date) -> bool:
        """Returns True if the item is now done, False if now undone."""
        existing = db_manager.execute_one(
            "SELECT id FROM study_completion WHERE userID=%s AND sourceID=%s AND completed_date=%s",
            (user_id, source_id, completed_date),
        )
        if existing:
            db_manager.execute_update(
                "DELETE FROM study_completion WHERE userID=%s AND sourceID=%s AND completed_date=%s",
                (user_id, source_id, completed_date),
            )
            return False
        else:
            db_manager.execute_insert(
                "INSERT INTO study_completion (completionID, userID, sourceID, completed_date, created, created_by) VALUES (%s,%s,%s,%s,NOW(),%s)",
                (str(uuid.uuid4()), user_id, source_id, completed_date, user_id),
            )
            return True

    # ------------------------------------------------------------------
    # Personal schedule
    # ------------------------------------------------------------------

    @staticmethod
    def set_personal_schedule(user_id: str, source_id: str, scheduled_date) -> None:
        existing = db_manager.execute_one(
            "SELECT id FROM study_schedule WHERE userID=%s AND sourceID=%s",
            (user_id, source_id),
        )
        if existing:
            db_manager.execute_update(
                "UPDATE study_schedule SET scheduled_date=%s WHERE userID=%s AND sourceID=%s",
                (scheduled_date, user_id, source_id),
            )
        else:
            db_manager.execute_insert(
                "INSERT INTO study_schedule (scheduleID, userID, sourceID, scheduled_date, created, created_by) VALUES (%s,%s,%s,%s,NOW(),%s)",
                (str(uuid.uuid4()), user_id, source_id, scheduled_date, user_id),
            )

    @staticmethod
    def clear_personal_schedule(user_id: str, source_id: str) -> None:
        db_manager.execute_update(
            "DELETE FROM study_schedule WHERE userID=%s AND sourceID=%s",
            (user_id, source_id),
        )

    @staticmethod
    def get_personal_scheduled_sources(user_id: str, source_ids: list[str], target_date) -> set[str]:
        if not source_ids:
            return set()
        placeholders = ','.join(['%s'] * len(source_ids))
        rows = db_manager.execute_query(
            f"SELECT sourceID FROM study_schedule WHERE userID=%s AND scheduled_date=%s AND sourceID IN ({placeholders})",
            (user_id, target_date, *source_ids),
        )
        return {r['sourceID'] for r in rows}

    @staticmethod
    def get_personal_schedule_for_sources(user_id: str, source_ids: list[str]) -> dict:
        """Return {sourceID: scheduled_date} for the given source IDs."""
        if not source_ids:
            return {}
        placeholders = ','.join(['%s'] * len(source_ids))
        rows = db_manager.execute_query(
            f"SELECT sourceID, scheduled_date FROM study_schedule WHERE userID=%s AND sourceID IN ({placeholders})",
            (user_id, *source_ids),
        )
        return {r['sourceID']: r['scheduled_date'] for r in rows}

    # ------------------------------------------------------------------
    # Daily calculation
    # ------------------------------------------------------------------

    @staticmethod
    def sources_for_date(subscription: dict, sources: list[dict],
                         target_date, user_id: str = None) -> list[dict]:
        filtered = StudyModel.get_filtered_sources(subscription, sources)
        if not filtered:
            return []

        # Personal schedule mode overrides collection mode
        if subscription.get('use_personal_schedule'):
            if not user_id:
                return []
            source_ids = [s['sourceID'] for s in filtered]
            scheduled = StudyModel.get_personal_scheduled_sources(user_id, source_ids, target_date)
            return [s for s in filtered if s['sourceID'] in scheduled]

        mode = subscription.get('mode')
        if mode == 'calendar':
            return [s for s in filtered if s.get('scheduled_date') == target_date]

        # Rate mode
        start = subscription.get('start_date')
        if start is None:
            return []
        if isinstance(start, str):
            start = date_cls.fromisoformat(start)
        days = (target_date - start).days
        if days < 0:
            return []
        per_day = subscription.get('per_day', 1) or 1
        repeat  = subscription.get('repeat', 1)

        if per_day > 0:
            # N items per day
            if not repeat:
                start_idx = days * per_day
                if start_idx >= len(filtered):
                    return []
                return filtered[start_idx:start_idx + per_day]
            else:
                start_idx = (days * per_day) % len(filtered)
                return [filtered[(start_idx + i) % len(filtered)] for i in range(per_day)]
        else:
            # Alternating days
            # -2 = even days: item on days 0, 2, 4… (starts on start_date)
            # -1 = odd days:  item on days 1, 3, 5… (starts one day after start_date)
            if per_day == -2:
                if days % 2 != 0:
                    return []
                item_idx = days // 2
            elif per_day == -1:
                if days % 2 != 1:
                    return []
                item_idx = (days - 1) // 2
            elif per_day == -7:
                if days % 7 != 0:
                    return []
                item_idx = days // 7
            else:
                return []
            if not repeat:
                if item_idx >= len(filtered):
                    return []
                return [filtered[item_idx]]
            else:
                return [filtered[item_idx % len(filtered)]]
