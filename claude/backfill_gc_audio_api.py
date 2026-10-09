#!/usr/bin/env python3
"""
Backfill audio_url for General Conference talks using the Church content API.

The API endpoint returns the MP3 URL directly — no browser needed.
Works for all years (1971–present).

Usage (from project root):
    python3 claude/backfill_gc_audio_api.py
    python3 claude/backfill_gc_audio_api.py --concurrency 20
    python3 claude/backfill_gc_audio_api.py --limit 50        # test run
    python3 claude/backfill_gc_audio_api.py --dry-run         # print without writing
"""

import argparse
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.services.database import db_manager

BASE = 'https://www.churchofjesuschrist.org'
API = BASE + '/study/api/v3/language-pages/type/content?lang=eng&uri='
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
    'Accept': 'application/json',
}

_db_lock = threading.Lock()
_counter = [0]
_total = [0]


def get_missing_sources(limit=None):
    sql = """
        SELECT ss.id, ss.url
        FROM study_source ss
        JOIN study_collection sc ON sc.collectionID = ss.collectionID
        WHERE sc.id = (SELECT MAX(s2.id) FROM study_collection s2
                       WHERE s2.collectionID = sc.collectionID)
          AND sc.name = 'General Conference'
          AND sc.name IS NOT NULL
          AND ss.title IS NOT NULL
          AND (ss.audio_url IS NULL OR ss.audio_url = '')
        ORDER BY ss.url
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    return db_manager.execute_query(sql, ())


def fetch_audio_url(url):
    """Return (audio_url_or_None, status)."""
    uri = url.replace(BASE + '/study', '')
    try:
        resp = requests.get(API + uri, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        audio_list = data.get('meta', {}).get('audio', []) or []
        if audio_list:
            return audio_list[0].get('mediaUrl'), 'ok'
        return None, 'no_audio'
    except requests.HTTPError as e:
        return None, f'http_{e.response.status_code}'
    except Exception as e:
        return None, f'error:{str(e)[:60]}'


def process_row(row, dry_run):
    row_id = row['id']
    url = row['url']
    audio_url, status = fetch_audio_url(url)

    if not dry_run and audio_url:
        with _db_lock:
            db_manager.execute_update(
                "UPDATE study_source SET audio_url = %s WHERE id = %s",
                (audio_url, row_id))
    elif not dry_run and status == 'no_audio':
        with _db_lock:
            db_manager.execute_update(
                "UPDATE study_source SET audio_url = 'none' WHERE id = %s",
                (row_id,))

    with _db_lock:
        _counter[0] += 1
        done = _counter[0]
        slug = url.split('/')[-1][:45]
        year = url.split('/')[-3] if len(url.split('/')) >= 3 else '????'
        if audio_url:
            tail = audio_url[-35:]
            print(f"  [{done:4d}/{_total[0]}] + {year} {slug:45s}  {tail}")
        else:
            print(f"  [{done:4d}/{_total[0]}] - {year} {slug:45s}  ({status})")

    return status, bool(audio_url)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--concurrency', type=int, default=10,
                        help='Parallel requests (default 10)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Max talks to process (for test runs)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Fetch but do not write to DB')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        rows = get_missing_sources(args.limit)

    _total[0] = len(rows)
    print(f"Talks with missing audio_url: {len(rows)}")
    print(f"Concurrency: {args.concurrency}{'  [DRY RUN]' if args.dry_run else ''}")
    if not rows:
        print("Nothing to do.")
        return

    start = time.time()
    ok = no_audio = errors = 0

    with app.app_context():
        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            futures = {executor.submit(process_row, row, args.dry_run): row
                       for row in rows}
            for future in as_completed(futures):
                status, had_audio = future.result()
                if had_audio:
                    ok += 1
                elif status == 'no_audio':
                    no_audio += 1
                else:
                    errors += 1

    elapsed = int(time.time() - start)
    print(f"\nDone in {elapsed}s: {ok} saved, {no_audio} no-audio, {errors} errors")


if __name__ == '__main__':
    main()
