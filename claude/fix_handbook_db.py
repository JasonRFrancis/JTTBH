#!/usr/bin/env python3
"""
One-time cleanup: remove the 174K duplicate subsection rows created by repeated
script restarts, then re-insert exactly one correct row per subsection.

Steps:
  1. DELETE all study_source rows for this collection where url contains '#'
  2. Fetch original chapter URLs from the DB (including soft-deleted chapters)
  3. For each chapter, fetch subsections from the Church API
  4. Insert one subsection source per h2 section, using existing MP3s for audio
  5. Soft-delete Chapter 16's original source (only chapter source still alive)

Run from project root:
    python3 claude/fix_handbook_db.py --dry-run
    python3 claude/fix_handbook_db.py
"""

import argparse
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.services.database import db_manager

COLLECTION_ID = '49dafe5a-1bf9-4ecb-9a18-2ea91b608c5f'
AUDIO_DIR = Path(__file__).parent.parent / 'app' / 'static' / 'audio' / 'handbook'
BASE_URL = 'https://www.churchofjesuschrist.org'
API_BASE = f'{BASE_URL}/study/api/v3/language-pages/type/content'


def get_original_chapters():
    """All distinct chapter URLs, including soft-deleted ones."""
    return db_manager.execute_query('''
        SELECT url, category, userID, MIN(order_by) AS order_by
        FROM study_source
        WHERE collectionID = %s
          AND url IS NOT NULL
          AND url NOT LIKE '%%#%%'
          AND category IS NOT NULL
        GROUP BY url, category, userID
        ORDER BY MIN(order_by)
    ''', (COLLECTION_ID,))


def get_alive_original_sources():
    """Chapter sources whose latest row still has a title (not yet soft-deleted)."""
    return db_manager.execute_query('''
        SELECT ss.sourceID, ss.userID, ss.category
        FROM study_source ss
        WHERE ss.collectionID = %s
          AND ss.id = (SELECT MAX(s2.id) FROM study_source s2 WHERE s2.sourceID = ss.sourceID)
          AND ss.title IS NOT NULL
          AND (ss.url IS NULL OR ss.url NOT LIKE '%%#%%')
          AND ss.category IS NOT NULL
    ''', (COLLECTION_ID,))


def fetch_api_body(page_url):
    path = page_url.replace(BASE_URL + '/study', '').split('?')[0]
    api_url = f'{API_BASE}?lang=eng&uri={path}'
    try:
        resp = requests.get(api_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        data = resp.json()
        return data.get('content', {}).get('body')
    except Exception as e:
        print(f'  API error: {e}')
        return None


def extract_subsections(body_html):
    soup = BeautifulSoup(body_html, 'html.parser')
    result = []
    for section in soup.find_all('section'):
        if section.find_parent('section'):
            continue
        h2 = section.find('h2')
        if not h2:
            continue
        for el in section.find_all('p', class_=re.compile(r'reference')):
            el.decompose()
        for el in section.find_all(['figure', 'img']):
            el.decompose()
        result.append({
            'fragment_id': h2.get('id', ''),
            'heading': h2.get_text(strip=True),
        })
    return result


def extract_chapter_num(category):
    m = re.match(r'Chapter\s+(\d+)', category or '')
    return int(m.group(1)) if m else None


def get_mp3_duration(path):
    try:
        out = subprocess.check_output(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', str(path)],
            stderr=subprocess.DEVNULL,
        )
        secs = float(out.strip())
        m, s = divmod(int(secs), 60)
        return f'{m}:{s:02d}'
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        # Step 1: delete all subsection rows
        count_row = db_manager.execute_one(
            "SELECT COUNT(*) AS cnt FROM study_source WHERE collectionID = %s AND url LIKE '%%#%%'",
            (COLLECTION_ID,)
        )
        dup_count = count_row['cnt']
        print(f'Step 1: DELETE {dup_count} subsection rows (url contains #)')
        if not args.dry_run:
            db_manager.execute_update(
                "DELETE FROM study_source WHERE collectionID = %s AND url LIKE '%%#%%'",
                (COLLECTION_ID,)
            )

        # Step 2: fetch original chapter URLs
        chapters = get_original_chapters()
        print(f'Step 2: {len(chapters)} original chapters to process')

        order_counter = 100
        total_inserted = 0

        for ch in chapters:
            chapter_num = extract_chapter_num(ch['category'])
            print(f'\n  {ch["category"]}: {ch["url"].split("/")[-1]}')

            body_html = fetch_api_body(ch['url'])
            if not body_html:
                print('    No API content, skipping')
                continue

            subsections = extract_subsections(body_html)
            if not subsections:
                print('    No h2 subsections, skipping')
                continue

            for i, sub in enumerate(subsections, start=1):
                subtitle = f'{chapter_num}.{i}' if chapter_num is not None else str(i)
                base_page = ch['url'].split('?')[0]
                page_url = f'{base_page}?lang=eng#{sub["fragment_id"]}'
                audio_filename = f'handbook_{chapter_num}_{i}.mp3'
                audio_path = AUDIO_DIR / audio_filename
                audio_url_val = f'/static/audio/handbook/{audio_filename}'

                duration = get_mp3_duration(audio_path) if audio_path.exists() else None
                exists_mark = '✓' if audio_path.exists() else '✗ MISSING'
                print(f'    [{subtitle}] {sub["heading"][:55]} [{exists_mark}]')

                if not args.dry_run:
                    new_id = str(uuid.uuid4())
                    db_manager.execute_insert('''
                        INSERT INTO study_source
                          (sourceID, collectionID, userID, title, subtitle, url,
                           audio_url, audio_length, category, order_by)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (new_id, COLLECTION_ID, ch['userID'],
                          sub['heading'], subtitle, page_url,
                          audio_url_val, duration, ch['category'], order_counter))

                order_counter += 1
                total_inserted += 1

            time.sleep(0.3)

        # Step 3: soft-delete any original chapter sources still alive
        alive = get_alive_original_sources()
        print(f'\nStep 3: Soft-delete {len(alive)} still-alive original chapter sources')
        for src in alive:
            print(f'  Soft-deleting {src["category"]} (sourceID={src["sourceID"]})')
            if not args.dry_run:
                db_manager.execute_insert(
                    'INSERT INTO study_source (sourceID, collectionID, userID, title, order_by) '
                    'VALUES (%s, %s, %s, NULL, 0)',
                    (src['sourceID'], COLLECTION_ID, src['userID']),
                )

        print(f'\nDone. {total_inserted} subsections {"would be " if args.dry_run else ""}inserted.')


if __name__ == '__main__':
    main()
