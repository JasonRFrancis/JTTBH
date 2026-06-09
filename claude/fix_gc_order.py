"""
Fix order_by for all talks in the "General Conference" collection.

Current state: order_by encodes only the within-conference position
(1, 2, 3… or 11, 12, 21, 22… for 2019+), so across the full collection
talks from every conference are interleaved.

New value: (year * 100 + month) * 1000 + old_order_by

  April 1971 talk 1  → 197104001
  April 1971 talk 45 → 197104045
  October 2025 talk 1 → 202510001

This gives chronological ordering across conferences while preserving
within-conference ordering.

Direct UPDATE used (insert-only pattern bypassed — same rationale as
fix_byu_speech_authors.py and set_gc_conference_labels.py).

Usage:
    python3 claude/fix_gc_order.py [--dry-run]
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def conference_date(url: str):
    """Return (year, month) or None."""
    m = re.search(r'/general-conference/(\d{4})/(\d{2})/', url)
    return (int(m.group(1)), int(m.group(2))) if m else None


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
            "SELECT id, url, order_by FROM study_source WHERE collectionID = %s AND title IS NOT NULL",
            (col['collectionID'],)
        )
        print(f"Found {len(sources)} sources")

        updates: list[tuple[int, int]] = []  # (new_order_by, id)
        no_match = []

        for s in sources:
            date = conference_date(s['url'] or '')
            if not date:
                no_match.append(s['id'])
                continue
            year, month = date
            new_order = (year * 100 + month) * 1000 + (s['order_by'] or 0)
            updates.append((new_order, s['id']))

        if args.dry_run:
            # Show a sample from a few conferences
            from collections import defaultdict
            by_conf: dict[str, list] = defaultdict(list)
            for new_order, sid in updates:
                conf = str(new_order // 1000)
                by_conf[conf].append(new_order % 1000)
            for conf in sorted(by_conf)[:5]:
                positions = sorted(by_conf[conf])
                year = int(conf) // 100
                month = int(conf) % 100
                print(f"  {month:02d}/{year}: positions {positions[:8]}{'…' if len(positions) > 8 else ''}")
            print(f"\nDRY RUN — {len(updates)} rows would be updated, {len(no_match)} skipped (no URL match)")
            return

        # Batch update
        for new_order, sid in updates:
            db_manager.execute_update(
                "UPDATE study_source SET `order_by` = %s WHERE id = %s",
                (new_order, sid)
            )

        print(f"Done. {len(updates)} rows updated.")
        if no_match:
            print(f"Warning: {len(no_match)} sources had no recognisable URL — order_by unchanged.")


if __name__ == '__main__':
    main()
