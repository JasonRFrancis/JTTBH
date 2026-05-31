#!/usr/bin/env python3
"""
Scrape Sefaria.org into study_collection / study_source tables.
One collection per section from sefaria.org/texts.

Granularity:
  Tanakh          — individual chapters (929)  + mechon-mamre audio
  Mishnah         — individual chapters (~524) per tractate
  Talmud          — individual tractates (Bavli + Yerushalmi combined)
  Tosefta         — individual tractates
  All others      — individual texts / books

Usage (from project root):
    python3 claude/scrape_sefaria.py
    python3 claude/scrape_sefaria.py --section Tanakh
    python3 claude/scrape_sefaria.py --section Mishnah
"""

import argparse
import os
import re
import sys
import time
import uuid

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.services.database import db_manager

SEFARIA   = 'https://www.sefaria.org'
SEFARIA_H = {'User-Agent': 'Mozilla/5.0 Chrome/120.0.0.0', 'Accept-Language': 'en-US'}
MM_BASE   = 'https://mechon-mamre.org/'
DELAY     = 0.5

ADMIN_USER_ID = None


# ---------------------------------------------------------------------------
# Tanakh book data
# (sefaria_name, section_label, num_chapters, mechon_mamre_name)
# ---------------------------------------------------------------------------
TANAKH_BOOKS = [
    # Torah
    ('Genesis',       'Torah',    50, 'Genesis'),
    ('Exodus',        'Torah',    40, 'Exodus'),
    ('Leviticus',     'Torah',    27, 'Leviticus'),
    ('Numbers',       'Torah',    36, 'Numbers'),
    ('Deuteronomy',   'Torah',    34, 'Deuteronomy'),
    # Nevi'im
    ('Joshua',        "Nevi'im",  24, 'Joshua'),
    ('Judges',        "Nevi'im",  21, 'Judges'),
    ('I Samuel',      "Nevi'im",  31, '1 Samuel'),
    ('II Samuel',     "Nevi'im",  24, '2 Samuel'),
    ('I Kings',       "Nevi'im",  22, '1 Kings'),
    ('II Kings',      "Nevi'im",  25, '2 Kings'),
    ('Isaiah',        "Nevi'im",  66, 'Isaiah'),
    ('Jeremiah',      "Nevi'im",  52, 'Jeremiah'),
    ('Ezekiel',       "Nevi'im",  48, 'Ezekiel'),
    ('Hosea',         "Nevi'im",  14, 'Hosea'),
    ('Joel',          "Nevi'im",   4, 'Joel'),
    ('Amos',          "Nevi'im",   9, 'Amos'),
    ('Obadiah',       "Nevi'im",   1, 'Obadiah'),
    ('Jonah',         "Nevi'im",   4, 'Jonah'),
    ('Micah',         "Nevi'im",   7, 'Micah'),
    ('Nahum',         "Nevi'im",   3, 'Nahum'),
    ('Habakkuk',      "Nevi'im",   3, 'Habakkuk'),
    ('Zephaniah',     "Nevi'im",   3, 'Zephaniah'),
    ('Haggai',        "Nevi'im",   2, 'Haggai'),
    ('Zechariah',     "Nevi'im",  14, 'Zechariah'),
    ('Malachi',       "Nevi'im",   3, 'Malachi'),
    # Ketuvim (Sefaria order)
    ('Psalms',        'Ketuvim', 150, 'Psalms'),
    ('Proverbs',      'Ketuvim',  31, 'Proverbs'),
    ('Job',           'Ketuvim',  42, 'Job'),
    ('Song of Songs', 'Ketuvim',   8, 'Song of Songs'),
    ('Ruth',          'Ketuvim',   4, 'Ruth'),
    ('Lamentations',  'Ketuvim',   5, 'Lamentations'),
    ('Ecclesiastes',  'Ketuvim',  12, 'Ecclesiastes'),
    ('Esther',        'Ketuvim',  10, 'Esther'),
    ('Daniel',        'Ketuvim',  12, 'Daniel'),
    ('Ezra',          'Ketuvim',  10, 'Ezra'),
    ('Nehemiah',      'Ketuvim',  13, 'Nehemiah'),
    ('I Chronicles',  'Ketuvim',  29, '1 Chronicles'),
    ('II Chronicles', 'Ketuvim',  36, '2 Chronicles'),
]


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def sefaria_api(path):
    time.sleep(DELAY)
    r = requests.get(SEFARIA + path, headers=SEFARIA_H, timeout=20)
    r.raise_for_status()
    return r.json()


def sefaria_url(title, chapter=None):
    slug = title.replace(' ', '_')
    if chapter:
        return f'{SEFARIA}/{slug}.{chapter}'
    return f'{SEFARIA}/{slug}'


# ---------------------------------------------------------------------------
# mechon-mamre audio map:  book_name → {chapter_num: mp3_url}
# ---------------------------------------------------------------------------

def load_mechon_mamre():
    r = requests.get('https://mechon-mamre.org/p/pt/ptmp3prq.htm',
                     headers=SEFARIA_H, timeout=15)
    soup = BeautifulSoup(r.content, 'html.parser', from_encoding='iso-8859-1')

    KNOWN = {
        'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
        'Joshua', 'Judges', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings',
        'Isaiah', 'Jeremiah', 'Ezekiel',
        'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah',
        'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
        '1 Chronicles', '2 Chronicles', 'Psalms', 'Job', 'Proverbs',
        'Ruth', 'Song of Songs', 'Ecclesiastes', 'Lamentations',
        'Esther', 'Daniel', 'Ezra', 'Nehemiah',
    }

    def clean(s):
        return re.sub(r'\s+', ' ', s.replace('\xa0', ' ').replace('Â', '')).strip()

    book_map = {}
    current = None
    for el in soup.body.descendants:
        if el.name == 'a' and el.get('href', '').endswith('.mp3'):
            if current is not None:
                chap = int(el.get_text(strip=True))
                href = el['href']
                if href.startswith('../../'):
                    href = MM_BASE + href[6:]
                book_map.setdefault(current, {})[chap] = href
        elif el.string:
            t = clean(el.string)
            if t in KNOWN:
                current = t
    return book_map


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

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
               author=None, category=None, subtitle=None, audio_url=None):
    if source_exists(collection_id, url):
        return False
    db_manager.execute_insert("""
        INSERT INTO study_source
          (sourceID, collectionID, userID, category, title, subtitle,
           author, url, audio_url, order_by, created, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
    """, (str(uuid.uuid4()), collection_id, ADMIN_USER_ID,
          category, title, subtitle, author, url, audio_url, order_by, ADMIN_USER_ID))
    return True


# ---------------------------------------------------------------------------
# Tanakh
# ---------------------------------------------------------------------------

def scrape_tanakh(mm_map):
    print("\n=== TANAKH ===")
    cid, created = get_or_create_collection(
        'Tanakh',
        'Hebrew Bible — Torah, Nevi\'im, Ketuvim — with audio from mechon-mamre.org')
    print(f"  Collection {'created' if created else 'exists'}: {cid[:8]}")

    order_counter = 0
    added = 0

    for book_num, (sf_name, section, num_chapters, mm_name) in enumerate(TANAKH_BOOKS, start=1):
        mm_chapters = mm_map.get(mm_name, {})
        for chap in range(1, num_chapters + 1):
            order_counter += 1
            url = sefaria_url(sf_name, chap)
            audio = mm_chapters.get(chap)
            title = f"{sf_name} {chap}"
            if add_source(cid, title=title, url=url, order_by=order_counter,
                          category=section, audio_url=audio):
                added += 1
        print(f"  {sf_name}: {num_chapters} chapters")

    total = sum(c for _, _, c, _ in TANAKH_BOOKS)
    print(f"  Total: {total} chapters, {added} added")


# ---------------------------------------------------------------------------
# Mishnah — chapter level per tractate
# ---------------------------------------------------------------------------

def scrape_mishnah(index):
    print("\n=== MISHNAH ===")
    cid, created = get_or_create_collection('Mishnah', 'Mishnah — six orders, chapter by chapter')
    print(f"  Collection {'created' if created else 'exists'}: {cid[:8]}")

    mishnah_section = next(s for s in index if s.get('category') == 'Mishnah')
    order_counter = 0
    added = 0

    for seder in mishnah_section.get('contents', []):
        seder_name = seder.get('category', '')
        for tractate in seder.get('contents', []):
            title = tractate.get('title', '')
            if not title or title == '?':
                continue
            # Get chapter count via shape API
            try:
                shape = sefaria_api(f'/api/shape/{title.replace(" ", "_")}')
                if isinstance(shape, list):
                    shape = shape[0]
                num_chapters = shape.get('length', 1)
            except Exception as e:
                print(f"  WARN: shape API for {title}: {e}")
                num_chapters = 1

            for chap in range(1, num_chapters + 1):
                order_counter += 1
                url = sefaria_url(title, chap)
                chap_title = f"{title}, Chapter {chap}"
                if add_source(cid, title=chap_title, url=url,
                              order_by=order_counter, category=seder_name):
                    added += 1
            print(f"  {title}: {num_chapters} chapters")

    print(f"  Total added: {added}")


# ---------------------------------------------------------------------------
# Flatten a section tree to leaf texts
# ---------------------------------------------------------------------------

def flatten_texts(items, parent_category=''):
    results = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if 'contents' in item:
            cat = item.get('category', parent_category)
            results.extend(flatten_texts(item['contents'], cat))
        elif 'title' in item and item['title'] and item['title'] != '?':
            results.append({
                'title':    item['title'],
                'heTitle':  item.get('heTitle', ''),
                'category': parent_category,
                'order':    item.get('order', 0),
                'desc':     item.get('enShortDesc', ''),
            })
    return results


# ---------------------------------------------------------------------------
# Talmud — tractate level (Bavli + Yerushalmi)
# ---------------------------------------------------------------------------

def scrape_talmud(index):
    print("\n=== TALMUD ===")
    cid, created = get_or_create_collection(
        'Talmud',
        'Babylonian and Jerusalem Talmud — tractate by tractate')
    print(f"  Collection {'created' if created else 'exists'}: {cid[:8]}")

    talmud_section = next(s for s in index if s.get('category') == 'Talmud')
    order_counter = 0
    added = 0

    for corpus in talmud_section.get('contents', []):
        corpus_name = corpus.get('category', '')
        for sub in corpus.get('contents', []):
            if 'contents' in sub:
                # nested order group
                for tractate in sub['contents']:
                    t = tractate.get('title', '')
                    if not t or t == '?': continue
                    order_counter += 1
                    if add_source(cid, title=t, url=sefaria_url(t),
                                  order_by=order_counter, category=corpus_name,
                                  subtitle=tractate.get('enShortDesc', '') or None):
                        added += 1
            else:
                t = sub.get('title', '')
                if not t or t == '?': continue
                order_counter += 1
                if add_source(cid, title=t, url=sefaria_url(t),
                              order_by=order_counter, category=corpus_name,
                              subtitle=sub.get('enShortDesc', '') or None):
                    added += 1

    print(f"  Total: {order_counter} tractates, {added} added")


# ---------------------------------------------------------------------------
# Generic section scraper — text level
# ---------------------------------------------------------------------------

def scrape_section(index, section_name, collection_name=None, description=None):
    print(f"\n=== {section_name.upper()} ===")
    name = collection_name or section_name
    cid, created = get_or_create_collection(name, description or name)
    print(f"  Collection {'created' if created else 'exists'}: {cid[:8]}")

    section = next((s for s in index if s.get('category') == section_name), None)
    if not section:
        print(f"  Section '{section_name}' not found in index")
        return

    texts = flatten_texts(section.get('contents', []))
    added = 0
    for i, text in enumerate(texts, start=1):
        if add_source(cid,
                      title=text['title'],
                      url=sefaria_url(text['title']),
                      order_by=i,
                      category=text['category'] or None,
                      subtitle=text['desc'] or None):
            added += 1

    print(f"  Total: {len(texts)} texts, {added} added")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

SECTION_RUNNERS = {
    'Tanakh':        None,   # special handler
    'Mishnah':       None,   # special handler
    'Talmud':        None,   # special handler
    'Tosefta':       ('Tosefta',       'Tosefta — tractate by tractate'),
    'Midrash':       ('Midrash',       'Midrash'),
    'Halakhah':      ('Halakhah',      'Halakhah — Jewish Law'),
    'Kabbalah':      ('Kabbalah',      'Kabbalah'),
    'Liturgy':       ('Liturgy',       'Liturgy'),
    'Jewish Thought':('Jewish Thought','Jewish Thought and Philosophy'),
    'Chasidut':      ('Chasidut',      'Chasidut'),
    'Musar':         ('Musar',         'Musar — Ethics and Self-Improvement'),
    'Responsa':      ('Responsa',      'Responsa — Halachic Questions and Answers'),
    'Second Temple': ('Second Temple', 'Second Temple Period Literature'),
    'Reference':     ('Reference',     'Reference Works'),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--section', default=None,
                        help='Only scrape one section (e.g. Tanakh, Mishnah, Talmud)')
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
        print(f"Admin user: {ADMIN_USER_ID[:8]}...")

        print("Loading mechon-mamre audio map...")
        mm_map = load_mechon_mamre()
        print(f"  {sum(len(v) for v in mm_map.values())} MP3s across {len(mm_map)} books")

        print("Loading Sefaria index...")
        index = sefaria_api('/api/index/')
        print(f"  {len(index)} top-level sections")

        sections_to_run = [args.section] if args.section else list(SECTION_RUNNERS.keys())

        for section in sections_to_run:
            if section not in SECTION_RUNNERS:
                print(f"Unknown section: {section}")
                continue
            if section == 'Tanakh':
                scrape_tanakh(mm_map)
            elif section == 'Mishnah':
                scrape_mishnah(index)
            elif section == 'Talmud':
                scrape_talmud(index)
            else:
                col_name, desc = SECTION_RUNNERS[section]
                scrape_section(index, section, col_name, desc)

    print("\nDone.")


if __name__ == '__main__':
    main()
