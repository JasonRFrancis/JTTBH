#!/usr/bin/env python3
"""
Expand General Handbook chapter sources into h2-level subsections and generate TTS audio.

For each chapter (0–38):
  1. Fetch the chapter body from the Church content API
  2. Extract top-level h2 sections
  3. Generate MP3 for each subsection via macOS `say` + ffmpeg
  4. Insert subsection sources into study_source
  5. Soft-delete the original chapter source

Title page and summary (no category) are left unchanged.
Chapters with no h2 subsections are skipped.

Usage:
    python3 claude/expand_handbook_subsections.py --dry-run
    python3 claude/expand_handbook_subsections.py --limit 2
    python3 claude/expand_handbook_subsections.py
    python3 claude/expand_handbook_subsections.py --voice Alex
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
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
DEFAULT_VOICE = 'Zoe (Premium)'


def get_handbook_sources():
    # Exclude subsection sources (already expanded — their URLs contain '#')
    return db_manager.execute_query('''
        SELECT ss.id, ss.sourceID, ss.userID, ss.title, ss.url, ss.order_by, ss.category
        FROM study_source ss
        WHERE ss.collectionID = %s
          AND ss.id = (SELECT MAX(s2.id) FROM study_source s2 WHERE s2.sourceID = ss.sourceID)
          AND ss.title IS NOT NULL
          AND (ss.url IS NULL OR ss.url NOT LIKE '%%#%%')
        ORDER BY ss.order_by
    ''', (COLLECTION_ID,))


def get_max_subsection_order():
    """Return the highest order_by already assigned to expanded subsection sources."""
    row = db_manager.execute_one('''
        SELECT MAX(ss.order_by) AS max_order
        FROM study_source ss
        WHERE ss.collectionID = %s
          AND ss.title IS NOT NULL
          AND ss.url LIKE '%%#%%'
    ''', (COLLECTION_ID,))
    return row['max_order'] if row and row['max_order'] else 99


def fetch_api_body(page_url):
    """Fetch body HTML from the Church content API for a handbook page URL."""
    # Strip /study prefix from page URL path for the API
    # https://www.churchofjesuschrist.org/study/manual/general-handbook/12-primary?lang=eng
    # → /manual/general-handbook/12-primary
    path = page_url.replace(BASE_URL + '/study', '').split('?')[0]
    api_url = f'{API_BASE}?lang=eng&uri={path}'
    try:
        resp = requests.get(api_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        data = resp.json()
        return data.get('content', {}).get('body')
    except Exception as e:
        print(f'  API error for {path}: {e}')
        return None


def extract_subsections(body_html):
    """Return list of dicts for each top-level h2 section in the body HTML."""
    soup = BeautifulSoup(body_html, 'html.parser')
    result = []
    for section in soup.find_all('section'):
        if section.find_parent('section'):
            continue
        h2 = section.find('h2')
        if not h2:
            continue
        fragment_id = h2.get('id', '')
        heading = h2.get_text(strip=True)
        # Remove citation/reference paragraphs and media before extracting text
        for el in section.find_all('p', class_=re.compile(r'reference')):
            el.decompose()
        for el in section.find_all(['figure', 'img']):
            el.decompose()
        text = re.sub(r'\s+', ' ', section.get_text(separator=' ', strip=True)).strip()
        result.append({'fragment_id': fragment_id, 'heading': heading, 'text': text})
    return result


def extract_chapter_num(category):
    """'Chapter 12' → 12; 'Chapter 0' → 0; None → None."""
    if not category:
        return None
    m = re.match(r'Chapter\s+(\d+)', category)
    return int(m.group(1)) if m else None


def format_duration(seconds):
    m, s = divmod(int(seconds), 60)
    return f'{m}:{s:02d}'


def get_mp3_duration(path):
    try:
        out = subprocess.check_output(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', str(path)],
            stderr=subprocess.DEVNULL,
        )
        return float(out.strip())
    except Exception:
        return 0.0


def generate_audio(tts_text, output_path, voice):
    """Generate MP3 at output_path from tts_text using say + ffmpeg."""
    with tempfile.NamedTemporaryFile(
        suffix='.txt', mode='w', encoding='utf-8', delete=False
    ) as f:
        f.write(tts_text)
        txt_path = f.name

    aiff_path = output_path.with_suffix('.aiff')
    try:
        subprocess.run(
            ['say', '-v', voice, '-f', txt_path, '-o', str(aiff_path)],
            check=True, capture_output=True,
        )
        subprocess.run(
            ['ffmpeg', '-y', '-i', str(aiff_path),
             '-codec:a', 'libmp3lame', '-qscale:a', '4', str(output_path)],
            check=True, capture_output=True,
        )
        return format_duration(get_mp3_duration(output_path))
    finally:
        os.unlink(txt_path)
        if aiff_path.exists():
            aiff_path.unlink()


def soft_delete_source(source_id, user_id):
    db_manager.execute_insert(
        'INSERT INTO study_source (sourceID, collectionID, userID, title, order_by) '
        'VALUES (%s, %s, %s, NULL, 0)',
        (source_id, COLLECTION_ID, user_id),
    )


def insert_subsection(user_id, title, subtitle, url, audio_url, audio_length, category, order_by):
    new_id = str(uuid.uuid4())
    db_manager.execute_insert('''
        INSERT INTO study_source
          (sourceID, collectionID, userID, title, subtitle, url,
           audio_url, audio_length, category, order_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (new_id, COLLECTION_ID, user_id, title, subtitle, url,
          audio_url, audio_length, category, order_by))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Print plan, do nothing')
    parser.add_argument('--limit', type=int, default=None, help='Process only N chapters')
    parser.add_argument('--voice', default=DEFAULT_VOICE, help='macOS say voice name')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        sources = get_handbook_sources()

        if not args.dry_run:
            AUDIO_DIR.mkdir(parents=True, exist_ok=True)

        # Title page (order_by=1) and summary (order_by=2) have no category; skip them.
        # Resume from after the highest order_by already assigned to subsection sources.
        order_counter = get_max_subsection_order() + 1
        processed = 0

        for source in sources:
            if source['category'] is None:
                print(f'Skip (no category): {source["title"]}')
                continue

            chapter_num = extract_chapter_num(source['category'])
            print(f'\n=== {source["category"]}: {source["title"]} ===')

            body_html = fetch_api_body(source['url'])
            if not body_html:
                print('  No API content, skipping')
                continue

            subsections = extract_subsections(body_html)
            if not subsections:
                print('  No h2 subsections found, skipping')
                continue

            print(f'  {len(subsections)} subsections')

            for i, sub in enumerate(subsections, start=1):
                subtitle = f'{chapter_num}.{i}' if chapter_num is not None else str(i)
                base_page = source['url'].split('?')[0]
                page_url = f'{base_page}?lang=eng#{sub["fragment_id"]}'
                audio_filename = f'handbook_{chapter_num}_{i}.mp3'
                audio_path = AUDIO_DIR / audio_filename
                audio_url_val = f'/static/audio/handbook/{audio_filename}'

                word_count = len(sub['text'].split())
                if args.dry_run:
                    print(f'  [{subtitle}] {sub["heading"][:60]} ({word_count}w) → #{sub["fragment_id"]}')
                    continue

                if audio_path.exists():
                    print(f'  [{subtitle}] {sub["heading"][:55]}... already done, skipping')
                    continue

                tts_text = f'Section {subtitle}: {sub["heading"]}. {sub["text"]}'
                print(f'  [{subtitle}] Generating: {sub["heading"][:55]}...', end='', flush=True)
                duration = generate_audio(tts_text, audio_path, args.voice)
                print(f' {duration}')

                insert_subsection(
                    user_id=source['userID'],
                    title=sub['heading'],
                    subtitle=subtitle,
                    url=page_url,
                    audio_url=audio_url_val,
                    audio_length=duration,
                    category=source['category'],
                    order_by=order_counter,
                )
                order_counter += 1

            if not args.dry_run:
                soft_delete_source(source['sourceID'], source['userID'])
                print(f'  Soft-deleted original, inserted {len(subsections)} subsections')

            processed += 1
            if args.limit and processed >= args.limit:
                print(f'\nReached --limit {args.limit}, stopping.')
                break

            time.sleep(0.5)

        print(f'\nDone. {processed} chapters processed.')


if __name__ == '__main__':
    main()
