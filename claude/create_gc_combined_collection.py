"""
Create a combined "General Conference" collection containing all talks
from all per-conference collections ("General Conference — Month YYYY").

In the combined collection:
  category  = conference label (e.g., "October 2025")
  subtitle  = original category (session name, e.g., "Saturday Morning Session")
  order_by  = (year * 100 + month) * 1000 + original_order_by

This lets subscribers filter to specific conferences via the category
checklist or "Category contains" text filter, while session info is
preserved in subtitle.

Usage:
    python3 claude/create_gc_combined_collection.py [--dry-run]
"""

import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

COMBINED_NAME = 'General Conference'
GC_PREFIX = 'General Conference — '  # em-dash

MONTHS = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4,
    'May': 5, 'June': 6, 'July': 7, 'August': 8,
    'September': 9, 'October': 10, 'November': 11, 'December': 12,
}


def parse_conference_label(name: str):
    """'General Conference — October 2025' → ('October 2025', 2025, 10) or None"""
    if not name.startswith(GC_PREFIX):
        return None
    label = name[len(GC_PREFIX):]
    m = re.match(r'^(\w+)\s+(\d{4})$', label)
    if not m:
        return None
    month = MONTHS.get(m.group(1))
    if not month:
        return None
    return label, int(m.group(2)), month


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    from app import create_app
    from app.services.database import db_manager

    app = create_app()
    with app.app_context():
        admin = db_manager.execute_one(
            "SELECT userID FROM `user` WHERE admin = 1 LIMIT 1", ()
        )
        if not admin:
            print("ERROR: no admin user")
            sys.exit(1)
        admin_id = admin['userID']

        gc_cols = db_manager.execute_query(
            """SELECT sc.collectionID, sc.name
               FROM study_collection sc
               WHERE sc.name LIKE 'General Conference — %%'
                 AND sc.id = (SELECT MAX(sc2.id) FROM study_collection sc2
                              WHERE sc2.collectionID = sc.collectionID)
                 AND sc.name IS NOT NULL
               ORDER BY sc.name""",
            ()
        )

        parsed = []
        for col in gc_cols:
            result = parse_conference_label(col['name'])
            if result:
                label, year, month = result
                parsed.append((col['collectionID'], label, year, month))

        print(f"Found {len(parsed)} General Conference collections")

        if args.dry_run:
            for cid, label, year, month in sorted(parsed, key=lambda x: (x[2], x[3])):
                n = db_manager.execute_one(
                    """SELECT COUNT(*) AS n FROM study_source ss
                       WHERE ss.collectionID = %s
                         AND ss.id = (SELECT MAX(ss2.id) FROM study_source ss2
                                      WHERE ss2.sourceID = ss.sourceID)
                         AND ss.title IS NOT NULL""",
                    (cid,)
                )['n']
                print(f"  {label}: {n} sources")
            total_src = sum(
                db_manager.execute_one(
                    """SELECT COUNT(*) AS n FROM study_source ss
                       WHERE ss.collectionID = %s
                         AND ss.id = (SELECT MAX(ss2.id) FROM study_source ss2
                                      WHERE ss2.sourceID = ss.sourceID)
                         AND ss.title IS NOT NULL""",
                    (cid,)
                )['n']
                for cid, *_ in parsed
            )
            print(f"\nDRY RUN — would create '{COMBINED_NAME}' with ~{total_src} sources")
            return

        # Get or create the combined collection
        existing = db_manager.execute_one(
            """SELECT sc.collectionID FROM study_collection sc
               WHERE sc.name = %s
                 AND sc.id = (SELECT MAX(sc2.id) FROM study_collection sc2
                              WHERE sc2.collectionID = sc.collectionID)
                 AND sc.name IS NOT NULL LIMIT 1""",
            (COMBINED_NAME,)
        )
        if existing:
            combined_id = existing['collectionID']
            print(f"Using existing '{COMBINED_NAME}': {combined_id[:8]}...")
        else:
            combined_id = str(uuid.uuid4())
            db_manager.execute_insert(
                """INSERT INTO study_collection
                     (collectionID, userID, name, description, mode, created, created_by)
                   VALUES (%s, %s, %s, %s, 'rate', NOW(), %s)""",
                (combined_id, admin_id,
                 COMBINED_NAME,
                 'All General Conference talks — filter by category to select specific conferences',
                 admin_id)
            )
            print(f"Created '{COMBINED_NAME}': {combined_id[:8]}...")

        total_added = 0
        total_skipped = 0

        for cid, label, year, month in sorted(parsed, key=lambda x: (x[2], x[3])):
            sources = db_manager.execute_query(
                """SELECT ss.title, ss.subtitle, ss.author, ss.url,
                          ss.audio_url, ss.audio_length, ss.order_by, ss.category
                   FROM study_source ss
                   WHERE ss.collectionID = %s
                     AND ss.id = (SELECT MAX(ss2.id) FROM study_source ss2
                                  WHERE ss2.sourceID = ss.sourceID)
                     AND ss.title IS NOT NULL
                   ORDER BY ss.order_by, ss.id""",
                (cid,)
            )

            base_order = (year * 100 + month) * 1000
            added = skipped = 0

            for s in sources:
                # Deduplicate by URL within the combined collection
                if s['url']:
                    exists = db_manager.execute_one(
                        """SELECT id FROM study_source
                           WHERE collectionID = %s AND url = %s AND title IS NOT NULL LIMIT 1""",
                        (combined_id, s['url'])
                    )
                    if exists:
                        skipped += 1
                        continue

                combined_order = base_order + (s.get('order_by') or 0)
                # Preserve session name (original category) in subtitle
                subtitle = s.get('category') or s.get('subtitle')

                db_manager.execute_insert(
                    """INSERT INTO study_source
                         (sourceID, collectionID, userID, category, title, subtitle,
                          author, url, audio_url, audio_length, order_by, created, created_by)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)""",
                    (str(uuid.uuid4()), combined_id, admin_id,
                     label,
                     s['title'],
                     subtitle,
                     s.get('author'),
                     s.get('url'),
                     s.get('audio_url'),
                     s.get('audio_length'),
                     combined_order,
                     admin_id)
                )
                added += 1

            total_added += added
            total_skipped += skipped
            print(f"  {label}: {added} added, {skipped} skipped")

        print(f"\nDone. {total_added} sources added, {total_skipped} already existed.")


if __name__ == '__main__':
    main()
