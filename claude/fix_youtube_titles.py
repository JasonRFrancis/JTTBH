"""
fix_youtube_titles.py — restore real titles for YouTube bookmarks whose
title was accidentally set to 'YouTube'.

Uses YouTube's free oEmbed endpoint — no API key required.

Usage (from project root on the server):
  python3 claude/fix_youtube_titles.py           # dry run
  python3 claude/fix_youtube_titles.py --fix     # apply updates
"""

import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import json

sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('config/.env')
from app.services.database import db_manager

DRY_RUN = '--fix' not in sys.argv
OEMBED  = 'https://www.youtube.com/oembed?format=json&url='


def fetch_title(url: str) -> str | None:
    try:
        req = urllib.request.Request(
            OEMBED + urllib.parse.quote(url, safe=''),
            headers={'User-Agent': 'Mozilla/5.0'},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return data.get('title', '').strip() or None
    except (urllib.error.HTTPError, urllib.error.URLError, Exception):
        return None


rows = db_manager.execute_query(
    "SELECT bookmarkID, url, title FROM bookmark "
    "WHERE title = 'YouTube' AND `read` = 0 "
    "AND (url LIKE %s OR url LIKE %s)",
    ('%youtube.com%', '%youtu.be%'),
)

print(f'Found {len(rows)} bookmark(s) with title = "YouTube"')
if DRY_RUN:
    print('DRY RUN — pass --fix to apply changes\n')

fixed = skipped = failed = 0

for i, row in enumerate(rows, 1):
    title = fetch_title(row['url'])
    status = f'[{i}/{len(rows)}]'

    if not title:
        print(f'{status} SKIP (no title returned)  {row["url"][:70]}')
        failed += 1
    elif DRY_RUN:
        print(f'{status} WOULD SET: {title!r}')
        print(f'         URL: {row["url"][:70]}')
        fixed += 1
    else:
        db_manager.execute_update(
            "UPDATE bookmark SET title = %s WHERE bookmarkID = %s",
            (title[:500], row['bookmarkID']),
        )
        print(f'{status} FIXED: {title!r}')
        fixed += 1

    time.sleep(0.15)  # be polite to YouTube's servers

print(f'\nDone. {"Would fix" if DRY_RUN else "Fixed"}: {fixed}  |  Failed: {failed}')
