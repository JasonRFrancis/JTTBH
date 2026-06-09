"""
Populate study_source.subtitle with the conference label (e.g. "April 2019")
for all talks in the "General Conference" collection.

The label is derived from the URL:
    .../general-conference/2019/04/... → "April 2019"

Direct UPDATE used (insert-only pattern bypassed — subtitle was never set
on import; same rationale as fix_byu_speech_authors.py).

Usage:
    python3 claude/set_gc_conference_labels.py [--dry-run]
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MONTH_NAMES = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December',
}


def conference_label(url: str) -> str | None:
    m = re.search(r'/general-conference/(\d{4})/(\d{2})/', url)
    if not m:
        return None
    year, month = int(m.group(1)), int(m.group(2))
    name = MONTH_NAMES.get(month)
    return f"{name} {year}" if name else None


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
        col = db_manager.execute_one(
            """SELECT sc.collectionID FROM study_collection sc
               WHERE sc.name = 'General Conference'
                 AND sc.id = (SELECT MAX(sc2.id) FROM study_collection sc2
                              WHERE sc2.collectionID = sc.collectionID)
                 AND sc.name IS NOT NULL LIMIT 1""",
            ()
        )
        if not col:
            print("ERROR: 'General Conference' collection not found.")
            sys.exit(1)

        sources = db_manager.execute_query(
            "SELECT id, url FROM study_source WHERE collectionID = %s AND title IS NOT NULL",
            (col['collectionID'],)
        )
        print(f"Found {len(sources)} sources")

        by_label: dict[str, list[int]] = {}
        no_match: list[int] = []
        for s in sources:
            label = conference_label(s['url'] or '')
            if label:
                by_label.setdefault(label, []).append(s['id'])
            else:
                no_match.append(s['id'])

        for label, ids in sorted(by_label.items()):
            print(f"  {label}: {len(ids)} talks")
        if no_match:
            print(f"  (no match): {len(no_match)} sources")

        total = sum(len(v) for v in by_label.values())
        if args.dry_run:
            print(f"\nDRY RUN — {total} rows would be updated")
            return

        updated = 0
        for label, ids in by_label.items():
            placeholders = ','.join(['%s'] * len(ids))
            db_manager.execute_update(
                f"UPDATE study_source SET subtitle = %s WHERE id IN ({placeholders})",
                (label, *ids)
            )
            updated += len(ids)

        print(f"\nDone. {updated} rows updated.")
        if no_match:
            print(f"Warning: {len(no_match)} sources had no recognisable URL — subtitle left blank.")


if __name__ == '__main__':
    main()
