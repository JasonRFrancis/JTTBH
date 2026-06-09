"""
Fix BYU Speeches sources — derive author from talk URL.

URLs follow the pattern:
    https://speeches.byu.edu/talks/{speaker-slug}/{talk-slug}/

The speaker slug is converted to a display name:
    theodore-a-tuttle → Theodore A. Tuttle
    adney-y-komatsu   → Adney Y. Komatsu

Direct UPDATE used (insert-only pattern bypassed — author was never
set on import and there is no correct prior state to preserve).

Usage:
    python3 claude/fix_byu_speech_authors.py [--dry-run]
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def slug_to_name(slug: str) -> str:
    """'theodore-a-tuttle' → 'Theodore A. Tuttle'"""
    parts = slug.split('-')
    return ' '.join(p.upper() + '.' if len(p) == 1 else p.capitalize() for p in parts)


def speaker_from_url(url: str) -> str | None:
    """Extract speaker display name from a BYU speeches URL."""
    m = re.search(r'speeches\.byu\.edu/talks/([^/]+)/', url)
    return slug_to_name(m.group(1)) if m else None


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
            "SELECT collectionID FROM study_collection WHERE name = 'BYU Speeches' AND name IS NOT NULL LIMIT 1",
            (),
        )
        if not col:
            print("ERROR: 'BYU Speeches' collection not found.")
            sys.exit(1)

        sources = db_manager.execute_query(
            """SELECT ss.id, ss.sourceID, ss.url
               FROM study_source ss
               WHERE ss.collectionID = %s
                 AND ss.title IS NOT NULL
                 AND (ss.author IS NULL OR ss.author = '')""",
            (col['collectionID'],),
        )

        print(f"Found {len(sources)} sources without an author")

        # Group by derived speaker name for dry-run summary
        by_speaker: dict[str, list] = {}
        no_match = []
        for s in sources:
            name = speaker_from_url(s['url'] or '')
            if name:
                by_speaker.setdefault(name, []).append(s['id'])
            else:
                no_match.append(s)

        if args.dry_run:
            for speaker, ids in sorted(by_speaker.items()):
                print(f"  {speaker}: {len(ids)} source{'s' if len(ids) != 1 else ''}")
            if no_match:
                print(f"  (no match): {len(no_match)} sources")
            print(f"\nDRY RUN — {len(sources) - len(no_match)} rows would be updated")
            return

        updated = 0
        for speaker, ids in by_speaker.items():
            placeholders = ','.join(['%s'] * len(ids))
            db_manager.execute_update(
                f"UPDATE study_source SET author = %s WHERE id IN ({placeholders})",
                (speaker, *ids),
            )
            updated += len(ids)

        print(f"Done. {updated} rows updated.")
        if no_match:
            print(f"Warning: {len(no_match)} sources had no recognisable BYU URL — author left blank.")


if __name__ == '__main__':
    main()
