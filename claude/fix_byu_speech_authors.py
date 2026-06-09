"""
Fix BYU Speeches sources — set author from collection name.

Direct UPDATE (insert-only pattern intentionally bypassed — this data
was simply never set on import and has no correct prior state to preserve).

Usage:
    python3 claude/fix_byu_speech_authors.py [--dry-run]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PREFIX = 'BYU Speeches — '


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
        if args.dry_run:
            rows = db_manager.execute_query("""
                SELECT sc.name, COUNT(*) AS n
                FROM study_source ss
                JOIN study_collection sc ON sc.collectionID = ss.collectionID
                WHERE sc.name LIKE 'BYU Speeches — %%'
                  AND ss.title IS NOT NULL
                  AND (ss.author IS NULL OR ss.author = '')
                GROUP BY sc.collectionID, sc.name
                ORDER BY sc.name
            """, ())
            total = sum(r['n'] for r in rows)
            for r in rows:
                speaker = r['name'][len(PREFIX):]
                print(f"  {speaker}: {r['n']} row{'s' if r['n'] != 1 else ''}")
            print(f"\nDRY RUN — {total} rows would be updated across {len(rows)} collections")
            return

        affected = db_manager.execute_update("""
            UPDATE study_source ss
            JOIN study_collection sc ON sc.collectionID = ss.collectionID
            SET ss.author = SUBSTRING(sc.name, %s)
            WHERE sc.name LIKE 'BYU Speeches — %%'
              AND ss.title IS NOT NULL
              AND (ss.author IS NULL OR ss.author = '')
        """, (len(PREFIX) + 1,))

        print(f"Done. {affected} rows updated.")


if __name__ == '__main__':
    main()
