#!/usr/bin/env python3
"""
Scrape BYU Speeches for General Conference speakers.

For every speaker who appears in both the GC collections and
speeches.byu.edu/speakers/, creates a collection
"BYU Speeches — {Speaker Name}" with one source per talk
(title, URL, date as subtitle, MP3 audio URL where available).

Usage:
    python3 claude/scrape_byu_speeches.py
    python3 claude/scrape_byu_speeches.py --dry-run   # show matches only
"""

import argparse
import os
import re
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.services.database import db_manager

BYU = 'https://speeches.byu.edu'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
           'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
DELAY = 0.6

ADMIN_USER_ID = None


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def fetch(url):
    time.sleep(DELAY)
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.content, 'html.parser')


# ---------------------------------------------------------------------------
# Name matching
# ---------------------------------------------------------------------------

def meaningful_first(s):
    """First name token longer than 1 char (skip leading initials like 'M.')."""
    for tok in s.lower().split():
        if len(tok.rstrip('.')) > 1:
            return tok.rstrip('.')
    return s.lower().split()[0].rstrip('.') if s.split() else ''


def parse_gc_name(name):
    """'Thomas S. Monson' → (last='monson', first_meaningful='thomas')"""
    parts = name.strip().rsplit(' ', 1)
    if len(parts) == 2:
        return parts[1].lower(), meaningful_first(parts[0])
    return name.lower(), ''


def parse_byu_name(text):
    """'Monson, Thomas S.  (15)' → (last='monson', first_meaningful='thomas', display, count)"""
    m = re.match(r'^(.+?)\s*\((\d+)\)$', text.strip())
    if not m:
        return None
    name_part = m.group(1).strip()
    count = int(m.group(2))
    comma = name_part.split(',', 1)
    if len(comma) == 2:
        last = comma[0].strip().lower()
        first = meaningful_first(comma[1])
    else:
        last = name_part.lower()
        first = ''
    return last, first, name_part, count


def load_byu_speakers():
    """Return {byu_url: (last, first_meaningful, display_name, count)}"""
    soup = fetch(f'{BYU}/speakers/')
    speakers = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        if not re.search(r'/speakers/[a-z]', href):
            continue
        parsed = parse_byu_name(a.get_text(strip=True))
        if parsed:
            last, first, display, count = parsed
            speakers[href] = (last, first, display, count)
    return speakers


def match_speakers(gc_authors, byu_speakers):
    """
    Returns list of (gc_name, byu_url, byu_display, byu_count).
    Matches on last name + first 4 chars of meaningful first name.
    """
    by_last = defaultdict(list)
    for url, (last, first, display, count) in byu_speakers.items():
        by_last[last].append((first, display, url, count))

    matches = []
    for gc_name in sorted(gc_authors):
        last, first = parse_gc_name(gc_name)
        candidates = by_last.get(last, [])
        for byu_first, byu_display, byu_url, byu_count in candidates:
            # Require at least 3 chars of first name to match (rejects M. vs M. false positives)
            gc_key = first[:4] if len(first) >= 3 else first
            byu_key = byu_first[:4] if len(byu_first) >= 3 else byu_first
            if gc_key and byu_key and gc_key == byu_key:
                matches.append((gc_name, byu_url, byu_display, byu_count))
                break

    return matches


# ---------------------------------------------------------------------------
# Talk scraping
# ---------------------------------------------------------------------------

MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
}

def parse_date(date_str):
    """'September 18, 2007' → (20070918, 'September 18, 2007')"""
    if not date_str:
        return 0, ''
    s = date_str.strip()
    m = re.match(r'(\w+)\s+(\d+),?\s+(\d{4})', s)
    if m:
        month = MONTHS.get(m.group(1).lower(), 0)
        day = int(m.group(2))
        year = int(m.group(3))
        return year * 10000 + month * 100 + day, s
    return 0, s


def scrape_speaker_talks(speaker_url):
    """
    Scrape all talks from a BYU speaker page.
    Returns list of (order_by_int, title, url, date_str, mp3_url_or_None).
    """
    soup = fetch(speaker_url)
    talks = []

    for card in soup.find_all('article', class_=re.compile(r'card')):
        # Title + URL
        h2 = card.find('h2', class_=re.compile(r'card__header'))
        if not h2:
            continue
        a = h2.find('a', href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        talk_url = a['href']

        # Date
        date_span = card.find('span', class_=re.compile(r'speech-date'))
        date_str = date_span.get_text(strip=True) if date_span else ''
        order_int, date_display = parse_date(date_str)

        # MP3 (inside download-links div, may be display:none but still in HTML)
        mp3_url = None
        for dl_a in card.find_all('a', download=True, href=True):
            href = dl_a['href']
            if href.lower().endswith('.mp3'):
                mp3_url = href
                break

        talks.append((order_int, title, talk_url, date_display, mp3_url))

    # Sort chronologically
    talks.sort(key=lambda x: x[0])
    return talks


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_gc_authors():
    rows = db_manager.execute_query("""
        SELECT DISTINCT ss.author FROM study_source ss
        JOIN study_collection sc ON sc.collectionID = ss.collectionID
        WHERE sc.name LIKE 'General Conference%%'
          AND ss.author IS NOT NULL AND ss.author != ''
    """, ())
    return {r['author'] for r in rows}


def get_or_create_collection(name, description=''):
    row = db_manager.execute_one("""
        SELECT sc.collectionID FROM study_collection sc
        WHERE sc.userID = %s AND sc.name = %s
          AND sc.id = (SELECT MAX(s2.id) FROM study_collection s2
                       WHERE s2.collectionID = sc.collectionID)
          AND sc.name IS NOT NULL LIMIT 1
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
    return bool(db_manager.execute_one(
        "SELECT id FROM study_source WHERE collectionID=%s AND url=%s AND title IS NOT NULL LIMIT 1",
        (collection_id, url)))


def add_source(collection_id, *, title, url, order_by,
               subtitle=None, audio_url=None, author=None):
    if source_exists(collection_id, url):
        return False
    db_manager.execute_insert("""
        INSERT INTO study_source
          (sourceID, collectionID, userID, title, subtitle, author,
           url, audio_url, order_by, created, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
    """, (str(uuid.uuid4()), collection_id, ADMIN_USER_ID,
          title, subtitle, author, url, audio_url, order_by, ADMIN_USER_ID))
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true',
                        help='Show matches without writing to DB')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        row = db_manager.execute_one(
            "SELECT userID FROM `user` WHERE admin = 1 LIMIT 1", ())
        if not row:
            print("ERROR: no admin user")
            sys.exit(1)
        global ADMIN_USER_ID
        ADMIN_USER_ID = row['userID']
        print(f"Admin: {ADMIN_USER_ID[:8]}...")

        print("Loading GC speakers from DB...")
        gc_authors = get_gc_authors()
        print(f"  {len(gc_authors)} unique GC speakers")

        print("Loading BYU speakers directory...")
        byu_speakers = load_byu_speakers()
        print(f"  {len(byu_speakers)} BYU speakers")

        matches = match_speakers(gc_authors, byu_speakers)
        print(f"\nMatched: {len(matches)} speakers\n")

        if args.dry_run:
            for gc_name, byu_url, byu_display, count in sorted(matches, key=lambda x: -x[3]):
                print(f"  {gc_name:40s}  {byu_display} ({count} talks)")
            return

        total_sources = 0
        for i, (gc_name, byu_url, byu_display, speech_count) in enumerate(matches, 1):
            col_name = f"BYU Speeches — {gc_name}"
            cid, created = get_or_create_collection(
                col_name,
                f'BYU devotional and forum speeches by {gc_name}')

            if not created:
                print(f"  [{i:3d}/{len(matches)}] {gc_name} (collection exists, skipping)")
                continue

            try:
                talks = scrape_speaker_talks(byu_url)
            except Exception as e:
                print(f"  [{i:3d}/{len(matches)}] ERROR {gc_name}: {e}")
                continue

            added = 0
            for order_by, title, talk_url, date_str, mp3_url in talks:
                if add_source(cid, title=title, url=talk_url,
                              order_by=order_by, subtitle=date_str or None,
                              audio_url=mp3_url or None, author=gc_name):
                    added += 1

            total_sources += added
            audio_count = sum(1 for _, _, _, _, mp3 in talks if mp3)
            print(f"  [{i:3d}/{len(matches)}] {gc_name}: {len(talks)} talks "
                  f"({audio_count} with audio) — {added} added")

        print(f"\nDone. Total sources added: {total_sources}")


if __name__ == '__main__':
    main()
