"""
Consolidate study collections.

Merges 110+ per-conference General Conference collections and 257 per-speaker
BYU Speeches collections each into a single collection.

Documented exception to insert-only: study_source.collectionID is updated
directly (like fitness_exercise catalog reorganization) so sourceIDs — and
therefore completion history — are preserved.

Run from the project root:
    python claude/consolidate_collections.py [--dry-run]
"""

import sys
import os
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app
from app.services.database import db_manager


def get_old_collection_ids(name_pattern: str) -> list[str]:
    """Return current (non-deleted) collectionIDs matching the name pattern."""
    rows = db_manager.execute_query("""
        SELECT DISTINCT sc.collectionID
        FROM study_collection sc
        WHERE sc.name LIKE %s
          AND sc.id = (SELECT MAX(sc2.id)
                       FROM study_collection sc2
                       WHERE sc2.collectionID = sc.collectionID)
          AND sc.name IS NOT NULL
    """, (name_pattern,))
    return [r['collectionID'] for r in rows]


def create_consolidated_collection(admin_user_id: str, name: str, description: str) -> str:
    collection_id = str(uuid.uuid4())
    db_manager.execute_insert(
        "INSERT INTO study_collection (collectionID, userID, name, description, mode, created, created_by) "
        "VALUES (%s, %s, %s, %s, 'rate', NOW(), %s)",
        (collection_id, admin_user_id, name, description, admin_user_id),
    )
    return collection_id


def soft_delete_collection(collection_id: str, admin_user_id: str):
    db_manager.execute_insert(
        "INSERT INTO study_collection (collectionID, userID, name, description, mode, created, created_by) "
        "VALUES (%s, %s, NULL, NULL, 'rate', NOW(), %s)",
        (collection_id, admin_user_id, admin_user_id),
    )


def consolidate(pattern: str, new_name: str, new_description: str,
                admin_user_id: str, dry_run: bool) -> dict:
    old_ids = get_old_collection_ids(pattern)
    if not old_ids:
        return {'old_count': 0, 'sources_moved': 0}

    # Count sources before
    placeholders = ','.join(['%s'] * len(old_ids))
    source_count_row = db_manager.execute_one(
        f"SELECT COUNT(*) AS cnt FROM study_source ss "
        f"WHERE ss.collectionID IN ({placeholders}) "
        f"AND ss.id = (SELECT MAX(ss2.id) FROM study_source ss2 WHERE ss2.sourceID = ss.sourceID) "
        f"AND ss.title IS NOT NULL",
        tuple(old_ids),
    )
    source_count = source_count_row['cnt'] if source_count_row else 0

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Consolidating {len(old_ids)} collections → \"{new_name}\"")
    print(f"  Sources to move: {source_count}")

    if dry_run:
        return {'old_count': len(old_ids), 'sources_moved': source_count}

    # Create new consolidated collection
    new_id = create_consolidated_collection(admin_user_id, new_name, new_description)
    print(f"  Created new collection: {new_id}")

    # Move all sources (direct UPDATE — documented exception)
    db_manager.execute_update(
        f"UPDATE study_source SET collectionID = %s WHERE collectionID IN ({placeholders})",
        (new_id, *old_ids),
    )
    print(f"  Moved {source_count} sources")

    # Delete old subscriptions (users must re-subscribe with smart filters)
    sub_result = db_manager.execute_update(
        f"DELETE FROM study_subscription WHERE collectionID IN ({placeholders})",
        tuple(old_ids),
    )
    print(f"  Deleted {sub_result} old subscriptions")

    # Soft-delete old collections
    for cid in old_ids:
        soft_delete_collection(cid, admin_user_id)
    print(f"  Soft-deleted {len(old_ids)} old collections")

    return {'old_count': len(old_ids), 'sources_moved': source_count, 'new_id': new_id}


def main():
    dry_run = '--dry-run' in sys.argv

    app = create_app()
    with app.app_context():
        # Get admin user
        admin = db_manager.execute_one(
            "SELECT userID, username FROM user WHERE admin = 1 ORDER BY created LIMIT 1", ()
        )
        if not admin:
            print("ERROR: No admin user found.")
            sys.exit(1)
        admin_user_id = admin['userID']
        print(f"Admin user: {admin['username']} ({admin_user_id})")

        # General Conference
        gc_result = consolidate(
            pattern='General Conference — %',
            new_name='General Conference',
            new_description='Talks from General Conference of The Church of Jesus Christ of Latter-day Saints, 1971–present. Filter by author (speaker) or category (conference date) to create a smart subscription.',
            admin_user_id=admin_user_id,
            dry_run=dry_run,
        )

        # BYU Speeches
        byu_result = consolidate(
            pattern='BYU Speeches — %',
            new_name='BYU Speeches',
            new_description='Devotional and forum addresses from Brigham Young University. Filter by author to subscribe to talks by a specific speaker.',
            admin_user_id=admin_user_id,
            dry_run=dry_run,
        )

        print("\n--- Summary ---")
        print(f"General Conference: merged {gc_result['old_count']} collections, {gc_result.get('sources_moved', 0)} sources")
        print(f"BYU Speeches: merged {byu_result['old_count']} collections, {byu_result.get('sources_moved', 0)} sources")
        if not dry_run:
            print("\nDone. Re-export study_data.sql for production:")
            print("  mysqldump -u <user> -p <db> study_collection study_source study_subscription study_completion study_schedule > study_data.sql")


if __name__ == '__main__':
    main()
