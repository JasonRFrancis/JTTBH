#!/usr/bin/env python3
"""
Scrape Lectures on Faith (lecturesonfaith.com) into study_collection/study_source.

The site is a client-rendered React SPA — plain requests only get an empty
<div id="root">, so this uses Playwright to render each page before reading
its structure.

Each of the 7 lectures is split into up to two sources:
  - the verses (the lecture text itself)
  - "Questions and Answers" — only lectures 1-5 have one; the Preface and
    Lectures 6-7 end without a Q&A section on this site.

Audio is intentionally left blank — to be generated later (same TTS approach
used for the General Handbook: macOS `say` + ffmpeg).

Run from project root:
    python3 claude/scrape_lectures_on_faith.py
    python3 claude/scrape_lectures_on_faith.py --dry-run
"""

import argparse
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.services.database import db_manager

BASE = 'https://lecturesonfaith.com'
SLUGS = ['preface', '1', '2', '3', '4', '5', '6', '7']

ADMIN_USER_ID = None


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def fetch_page(page, slug):
    """Render one lecture page and return its title/subtitle/hasQA."""
    page.goto(f'{BASE}/{slug}', timeout=30000)
    page.wait_for_selector('article h1', timeout=15000)
    return page.evaluate("""() => {
        const article = document.querySelector('article');
        const h1 = document.querySelector('h1');
        const subtitleEl = document.querySelector('header p');
        const text = article.innerText;
        return {
            title: h1 ? h1.textContent.replace(/\\s+/g, ' ').trim() : null,
            subtitle: subtitleEl ? subtitleEl.textContent.trim() : '',
            hasQA: text.includes('Questions and Answers'),
        };
    }""")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_or_create_collection(name, description=''):
    row = db_manager.execute_one("""
        SELECT sc.collectionID FROM study_collection sc
        WHERE sc.userID = %s AND sc.name = %s
          AND sc.id = (SELECT MAX(s2.id) FROM study_collection s2
                       WHERE s2.collectionID = sc.collectionID)
          AND sc.name IS NOT NULL
        LIMIT 1
    """, (ADMIN_USER_ID, name))
    if row:
        return row['collectionID'], False
    cid = str(uuid.uuid4())
    db_manager.execute_insert("""
        INSERT INTO study_collection
          (collectionID, userID, name, description, mode, created, created_by)
        VALUES (%s, %s, %s, %s, 'rate', NOW(), %s)
    """, (cid, ADMIN_USER_ID, name, description or name, ADMIN_USER_ID))
    return cid, True


def source_exists(collection_id, url):
    row = db_manager.execute_one(
        "SELECT id FROM study_source WHERE collectionID=%s AND url=%s AND title IS NOT NULL LIMIT 1",
        (collection_id, url))
    return bool(row)


def add_source(collection_id, *, title, url, order_by, category=None):
    if source_exists(collection_id, url):
        return False
    db_manager.execute_insert("""
        INSERT INTO study_source
          (sourceID, collectionID, userID, category, title, order_by, url, created, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
    """, (str(uuid.uuid4()), collection_id, ADMIN_USER_ID, category, title,
          order_by, url, ADMIN_USER_ID))
    return True


# ---------------------------------------------------------------------------
# Scrape
# ---------------------------------------------------------------------------

def scrape(dry_run=False):
    from playwright.sync_api import sync_playwright

    if dry_run:
        existing = db_manager.execute_one("""
            SELECT sc.collectionID FROM study_collection sc
            WHERE sc.userID = %s AND sc.name = 'Lectures on Faith'
              AND sc.id = (SELECT MAX(s2.id) FROM study_collection s2
                           WHERE s2.collectionID = sc.collectionID)
              AND sc.name IS NOT NULL
        """, (ADMIN_USER_ID,))
        cid = existing['collectionID'] if existing else None
        print(f"Collection {'exists' if existing else 'would be created'}"
              + (f": {cid[:8]}" if cid else ""))
    else:
        cid, created = get_or_create_collection(
            'Lectures on Faith',
            'The Lectures on Faith, delivered to the School of the Prophets in '
            'Kirtland, Ohio. Each lecture is split into its verses and (where '
            'present) its closing Questions and Answers section.',
        )
        print(f"Collection {'created' if created else 'exists'}: {cid[:8]}")

    order = 0
    added = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for slug in SLUGS:
            try:
                info = fetch_page(page, slug)
            except Exception as e:
                print(f"  WARN: {slug}: {e}")
                continue

            if not info['title']:
                print(f"  WARN: {slug}: no title found, skipping")
                continue

            category = info['subtitle'] or None
            order += 1
            label = f" ({category})" if category else ""

            if dry_run:
                print(f"  [{order}] {info['title']}{label}")
            elif add_source(cid, title=info['title'], url=f'{BASE}/{slug}',
                            order_by=order, category=category):
                print(f"  + [{order}] {info['title']}{label}")
                added += 1

            if info['hasQA']:
                order += 1
                if dry_run:
                    print(f"  [{order}] Questions and Answers{label}")
                elif add_source(cid, title='Questions and Answers',
                                url=f'{BASE}/{slug}#q1', order_by=order,
                                category=category):
                    print(f"  + [{order}] Questions and Answers{label}")
                    added += 1

        browser.close()

    verb = 'Would add' if dry_run else 'Added'
    print(f"\n{verb} {added} sources.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Print without writing')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        row = db_manager.execute_one(
            "SELECT userID FROM `user` WHERE admin = 1 LIMIT 1", ())
        if not row:
            print("ERROR: no admin user found in database")
            sys.exit(1)
        global ADMIN_USER_ID
        ADMIN_USER_ID = row['userID']
        print(f"Admin user: {ADMIN_USER_ID[:8]}...")

        scrape(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
