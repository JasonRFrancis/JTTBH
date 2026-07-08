#!/usr/bin/env python3
"""
Check speeches.byu.edu, byui.edu/speeches, and General Conference for new
material and add it to the database. Safe to re-run on a schedule — only
adds talks not already present (by URL).

Usage:
    python3 claude/import_new_speeches.py                # all three sources
    python3 claude/import_new_speeches.py --site byu
    python3 claude/import_new_speeches.py --site byui
    python3 claude/import_new_speeches.py --site gc
    python3 claude/import_new_speeches.py --dry-run       # byu/byui only; GC has no preview mode
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.services.database import db_manager

import scrape_byu_speeches
import scrape_byui_speeches
import scrape_gospel_library


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', choices=['byu', 'byui', 'gc', 'all'], default='all')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show matches without writing to DB (byu/byui only)')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        row = db_manager.execute_one(
            "SELECT userID FROM `user` WHERE admin = 1 LIMIT 1", ())
        if not row:
            print("ERROR: no admin user")
            sys.exit(1)
        admin_id = row['userID']
        # add_source/get_or_create_collection are shared functions defined in
        # scrape_byu_speeches and imported by name into scrape_byui_speeches,
        # so setting the global here is enough for both modules.
        scrape_byu_speeches.ADMIN_USER_ID = admin_id
        scrape_gospel_library.ADMIN_USER_ID = admin_id
        print(f"Admin: {admin_id[:8]}...")

        if args.site in ('byu', 'all'):
            print("\n=== speeches.byu.edu ===")
            scrape_byu_speeches.run_import(dry_run=args.dry_run)

        if args.site in ('byui', 'all'):
            print("\n=== byui.edu/speeches ===")
            scrape_byui_speeches.run_import(dry_run=args.dry_run)

        if args.site in ('gc', 'all'):
            print("\n=== General Conference ===")
            if args.dry_run:
                print("  (no preview mode for General Conference — skipping; "
                      "run without --dry-run to check)")
            else:
                scrape_gospel_library.scrape_gc()


if __name__ == '__main__':
    main()
