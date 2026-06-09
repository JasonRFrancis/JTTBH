"""
Show all subscriptions for the admin user and explain why each
does or doesn't produce items for today.

Usage:
    python3 claude/diagnose_subscriptions.py
    python3 claude/diagnose_subscriptions.py byu   # filter by keyword
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    keyword = sys.argv[1].lower() if len(sys.argv) > 1 else ''

    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    from app import create_app
    from app.services.database import db_manager
    from app.models.study_model import StudyModel
    from app.services.timezone_utils import today_for_tz

    app = create_app()
    with app.app_context():
        admin = db_manager.execute_one(
            "SELECT userID, username FROM `user` WHERE admin=1 LIMIT 1", ()
        )
        user_id = admin['userID']
        pref = db_manager.execute_one(
            "SELECT value FROM user_preference WHERE userID=%s AND `key`='timezone' LIMIT 1",
            (user_id,)
        )
        tz = (pref['value'] if pref else None) or 'UTC'
        today    = today_for_tz(tz)
        print(f"User: {admin['username']}  today: {today}  tz: {tz}\n")

        subs = StudyModel.get_user_subscriptions(user_id)
        if keyword:
            subs = [s for s in subs if keyword in (s.get('subscription_name') or '').lower()
                    or keyword in (s.get('collection_name') or '').lower()]

        print(f"{len(subs)} subscription(s) matched\n")

        for s in subs:
            label = s.get('subscription_name') or s['collection_name']
            sources  = StudyModel.get_sources(s['collectionID'])
            filtered = StudyModel.get_filtered_sources(s, sources)
            items    = StudyModel.sources_for_date(s, sources, today, user_id)

            status = 'OK — items today' if items else 'EMPTY — no items today'
            print(f"[{status}] {label}")
            print(f"  collectionID : {s['collectionID'][:8]}...")
            print(f"  collection   : {s['collection_name']}")
            print(f"  total sources: {len(sources)}  after filters: {len(filtered)}  today: {len(items)}")
            print(f"  start_date={s['start_date']}  per_day={s['per_day']}  start_offset={s['start_offset'] or 0}  repeat={s.get('repeat')}  mode={s['mode']}")

            active_filters = []
            if s.get('filter_author'):      active_filters.append(f"author={repr(s['filter_author'])}")
            if s.get('filter_category'):    active_filters.append(f"category={repr(s['filter_category'])}")
            if s.get('filter_has_audio'):   active_filters.append("has_audio=1")
            if s.get('filter_title'):       active_filters.append(f"title={repr(s['filter_title'])}")
            if s.get('filter_author_text'): active_filters.append(f"author_text={repr(s['filter_author_text'])}")
            if s.get('filter_category_text'): active_filters.append(f"category_text={repr(s['filter_category_text'])}")
            if s.get('filter_subtitle_text'): active_filters.append(f"subtitle_text={repr(s['filter_subtitle_text'])}")
            if active_filters:
                print(f"  filters      : {', '.join(active_filters)}")
            else:
                print(f"  filters      : (none)")

            if not items and filtered:
                # Show why sources_for_date returned nothing despite items existing
                from datetime import date as date_cls
                start = s.get('start_date')
                if start is None:
                    print(f"  PROBLEM: start_date is NULL")
                else:
                    if isinstance(start, str):
                        start = date_cls.fromisoformat(start)
                    days = (today - start).days
                    print(f"  days since start_date: {days}")
                    if days < 0:
                        print(f"  PROBLEM: start_date is in the future")

            print()


if __name__ == '__main__':
    main()
