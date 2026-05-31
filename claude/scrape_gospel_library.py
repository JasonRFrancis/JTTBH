#!/usr/bin/env python3
"""
Scrape Gospel Library — Scriptures + General Conference.
Populates study_collection and study_source tables.

Run from project root:
    python3 claude/scrape_gospel_library.py
    python3 claude/scrape_gospel_library.py --scripture-only
    python3 claude/scrape_gospel_library.py --gc-only --start-year=2020
"""

import argparse
import os
import re
import sys
import time
import uuid
from datetime import date

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.services.database import db_manager

BASE = 'https://www.churchofjesuschrist.org'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}
DELAY = 0.75

STANDARD_WORKS = [
    ('Old Testament',          '/study/scriptures/ot'),
    ('New Testament',          '/study/scriptures/nt'),
    ('Book of Mormon',         '/study/scriptures/bofm'),
    ('Doctrine and Covenants', '/study/scriptures/dc-testament'),
    ('Pearl of Great Price',   '/study/scriptures/pgp'),
]

SESSION_NAMES = {
    1: 'Saturday Morning Session',
    2: 'Saturday Afternoon Session',
    3: 'Saturday Evening Session',
    4: 'Sunday Morning Session',
    5: 'Sunday Afternoon Session',
}

ADMIN_USER_ID = None


# ---------------------------------------------------------------------------
# HTTP + parsing
# ---------------------------------------------------------------------------

def fetch(path):
    url = BASE + path if path.startswith('/') else path
    sep = '&' if '?' in url else '?'
    url += sep + 'lang=eng'
    time.sleep(DELAY)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.content, 'html.parser', from_encoding='utf-8')


def clean(s):
    """Normalize whitespace and remove Mojibake NBSP artifacts."""
    if not s:
        return ''
    s = s.replace('Â ', ' ').replace(' ', ' ')
    return ' '.join(s.split()).strip()


def extract_link_text(a_el):
    """
    Return (title, subtitle) from a Gospel Library <a> element.
    Structure: <a><div><p><span>TITLE</span></p><p class="subtitle-...">SUBTITLE</p></div></a>
    """
    div = a_el.find('div')
    if div:
        paras = div.find_all('p', recursive=False)
        title = clean(paras[0].get_text()) if paras else ''
        subtitle = clean(paras[1].get_text()) if len(paras) > 1 else None
    else:
        title = clean(a_el.get_text())
        subtitle = None
    return title, subtitle


def href_base(a_el):
    return a_el['href'].split('?')[0].rstrip('/')


def build_link_map(soup):
    """Return {href_without_query: a_el} for all <a> tags with href."""
    m = {}
    for a in soup.find_all('a', href=True):
        h = href_base(a)
        if h not in m:
            m[h] = a
    return m


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


def source_exists(collection_id, url_base):
    row = db_manager.execute_one(
        "SELECT id FROM study_source WHERE collectionID=%s AND url=%s AND title IS NOT NULL LIMIT 1",
        (collection_id, url_base))
    return bool(row)


def add_source(collection_id, *, title, url, order_by,
               author=None, category=None, subtitle=None):
    url_base = url.split('?')[0]
    if source_exists(collection_id, url_base):
        return False
    db_manager.execute_insert("""
        INSERT INTO study_source
          (sourceID, collectionID, userID, category, title, subtitle,
           author, url, order_by, created, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
    """, (str(uuid.uuid4()), collection_id, ADMIN_USER_ID,
          category, title, subtitle, author, url_base, order_by, ADMIN_USER_ID))
    return True


# ---------------------------------------------------------------------------
# Scriptures
# ---------------------------------------------------------------------------

def scrape_standard_work(work_name, work_path):
    print(f"\n  {work_name}")
    cid, created = get_or_create_collection(work_name, f'Scriptures — {work_name}')
    if not created:
        print(f"    (collection exists, checking for new sources)")

    soup = fetch(work_path)
    link_map = build_link_map(soup)

    # Collect multi-chapter book hrefs (1 segment, non-numeric) from the index page
    multi_book_hrefs = set()
    for href in link_map:
        if href.startswith(work_path + '/'):
            rel = href[len(work_path) + 1:]
            parts = rel.split('/')
            if len(parts) == 1 and not parts[0].isdigit():
                multi_book_hrefs.add(href)

    # Build ordered item list in DOM order, combining multi-chapter books
    # and single-chapter books (which appear as /book/1 links whose parent
    # is NOT a multi-chapter book)
    seen = set()
    items = []  # ('multi'|'single', href)
    for a in soup.find_all('a', href=True):
        h = href_base(a)
        if h in seen or not h.startswith(work_path + '/'):
            continue
        seen.add(h)

        rel = h[len(work_path) + 1:]
        parts = rel.split('/')

        if len(parts) == 1 and not parts[0].isdigit():
            items.append(('multi', h))
        elif len(parts) == 2 and parts[1].isdigit():
            parent = work_path + '/' + parts[0]
            if parent not in multi_book_hrefs:
                # Single-chapter book (e.g. /bofm/enos/1)
                items.append(('single', h))
            # else: chapter of a multi-chapter book — fetched via book page

    order_counter = 0
    added_total = 0

    for item_type, href in items:
        if item_type == 'single':
            a_el = link_map.get(href)
            title, subtitle = extract_link_text(a_el) if a_el else (href.split('/')[-2], None)
            title = title or href.split('/')[-2]
            order_counter += 1
            if add_source(cid, title=title, url=BASE + href,
                          order_by=order_counter, category=title, subtitle=subtitle):
                print(f"    + {title}")
                added_total += 1

        else:  # multi-chapter book
            a_el = link_map.get(href)
            book_name, _ = extract_link_text(a_el) if a_el else (href.split('/')[-1], None)
            book_name = book_name.split('\n')[0].strip()

            if not book_name:
                continue  # front matter (title-page, introduction, testimonies, etc.)

            try:
                book_soup = fetch(href)
            except Exception as e:
                print(f"    WARN: {href}: {e}")
                continue

            chap_pat = re.compile(r'^' + re.escape(href) + r'/(\d+)$')
            chapters = []
            seen_chaps = set()
            for ca in book_soup.find_all('a', href=True):
                chap_href = href_base(ca)
                if chap_href in seen_chaps:
                    continue
                m = chap_pat.match(chap_href)
                if m:
                    seen_chaps.add(chap_href)
                    chap_num = int(m.group(1))
                    title, subtitle = extract_link_text(ca)
                    if not title or title.isdigit():
                        title = f"{book_name} {chap_num}"
                    chapters.append((chap_num, chap_href, title, subtitle))

            chapters.sort(key=lambda x: x[0])

            new_in_book = 0
            for chap_num, chap_href, title, subtitle in chapters:
                order_counter += 1
                if add_source(cid, title=title, url=BASE + chap_href,
                              order_by=order_counter, category=book_name,
                              subtitle=subtitle):
                    new_in_book += 1
                    added_total += 1

            if not chapters:
                continue  # reference/front-matter page with no numbered chapters
            status = f"{new_in_book} new" if new_in_book else "exists"
            print(f"    {book_name}: {len(chapters)} chapters ({status})")

    print(f"    Total added: {added_total}")
    return added_total


def scrape_scriptures():
    print("\n=== SCRIPTURES ===")
    for work_name, work_path in STANDARD_WORKS:
        scrape_standard_work(work_name, work_path)


# ---------------------------------------------------------------------------
# General Conference
# ---------------------------------------------------------------------------

# 2019+: /YYYY/MM/NNspeaker — numeric prefix encodes session and order
NUMERIC_PAT = re.compile(r'^/study/general-conference/\d{4}/\d{2}/(\d+)([a-z][-a-z0-9]*)$')
# pre-2019: /YYYY/MM/talk-title-slug — DOM order gives sequence
SLUG_PAT = re.compile(r'^/study/general-conference/\d{4}/\d{2}/([a-z][a-z0-9-]+)$')


def parse_gc_page(soup):
    """
    Returns list of (order_by, href, title, author, session_label) in order.
    Handles both numeric-prefix (2019+) and slug (pre-2019) URL formats.
    """
    # Try numeric format first
    numeric_items = []
    seen = set()
    for a in soup.find_all('a', href=True):
        h = href_base(a)
        if h in seen:
            continue
        m = NUMERIC_PAT.match(h)
        if m:
            seen.add(h)
            prefix = int(m.group(1))
            title, author = extract_link_text(a)
            session_num = prefix // 10
            numeric_items.append((
                prefix, h,
                title or h.split('/')[-1], author,
                SESSION_NAMES.get(session_num, f'Session {session_num}'),
            ))

    if numeric_items:
        return sorted(numeric_items)

    # Fall back to slug format (pre-2019): session headers appear as links with no author
    slug_items = []
    seen2 = set()
    current_session = 'Saturday Morning Session'
    order_counter = 0
    for a in soup.find_all('a', href=True):
        h = href_base(a)
        if h in seen2 or not SLUG_PAT.match(h):
            continue
        seen2.add(h)
        title, author = extract_link_text(a)
        if not author:
            # Session header (e.g., "Saturday Morning Session")
            if title:
                current_session = title
        else:
            order_counter += 1
            slug_items.append((order_counter, h, title or h.split('/')[-1], author, current_session))

    return slug_items


def scrape_gc(start_year=1971, end_year=None):
    today = date.today()
    if end_year is None:
        end_year = today.year

    print(f"\n=== GENERAL CONFERENCE {start_year}–{end_year} ===")
    total_added = 0

    for year in range(start_year, end_year + 1):
        for month in ('04', '10'):
            if date(year, int(month), 1) > today:
                continue

            conf_path = f'/study/general-conference/{year}/{month}'
            month_name = 'April' if month == '04' else 'October'
            conf_name = f"General Conference — {month_name} {year}"

            try:
                soup = fetch(conf_path)
            except requests.HTTPError as e:
                if e.response.status_code == 404:
                    continue
                print(f"  ERROR {year}/{month}: {e}")
                continue
            except Exception as e:
                print(f"  ERROR {year}/{month}: {e}")
                continue

            talks = parse_gc_page(soup)
            if not talks:
                continue

            cid, created = get_or_create_collection(conf_name)

            conf_added = 0
            for order_by, h, title, author, session_label in talks:
                if add_source(cid, title=title, author=author,
                              url=BASE + h, order_by=order_by, category=session_label):
                    conf_added += 1

            total_added += conf_added
            marker = 'NEW' if created else ('updated' if conf_added else 'exists')
            print(f"  {conf_name}: {len(talks)} talks, {conf_added} added [{marker}]")

    print(f"\nTotal GC sources added: {total_added}")


# ---------------------------------------------------------------------------
# General Handbook
# ---------------------------------------------------------------------------

HANDBOOK_INDEX = '/study/manual/general-handbook'
HANDBOOK_PAT = re.compile(r'^/study/manual/general-handbook/([^/#]+)$')


def _handbook_chapter_num(slug):
    """Extract sort key: title-page → -2, summary → -1, chapters → chapter number."""
    if slug == 'title-page':
        return -2.0
    if slug == 'summary-of-recent-updates':
        return -1.0
    m = re.match(r'^(\d+)', slug)
    return float(m.group(1)) if m else 999.0


def scrape_handbook():
    print("\n=== GENERAL HANDBOOK ===")
    soup = fetch(HANDBOOK_INDEX)

    # Collect all chapter links in DOM order, deduplicate by slug
    seen = set()
    chapters = []  # (slug, href)
    for a in soup.find_all('a', href=True):
        h = href_base(a)
        m = HANDBOOK_PAT.match(h)
        if not m:
            continue
        slug = m.group(1)
        if slug in seen:
            continue
        seen.add(slug)
        chapters.append((slug, h))

    # Sort by chapter number
    chapters.sort(key=lambda x: _handbook_chapter_num(x[0]))
    print(f"  Found {len(chapters)} chapters — fetching titles...")

    cid, created = get_or_create_collection(
        'General Handbook',
        'General Handbook: Serving in The Church of Jesus Christ of Latter-day Saints',
    )
    print(f"  Collection {'created' if created else 'exists'}: {cid[:8]}")

    added = 0
    for order_by, (slug, href) in enumerate(chapters, start=1):
        # Fetch the chapter page for its h1 title
        try:
            chapter_soup = fetch(href)
        except Exception as e:
            print(f"  WARN: {slug}: {e}")
            continue

        h1 = chapter_soup.find('h1')
        title = clean(h1.get_text()) if h1 else slug.replace('-', ' ').title()

        # Use chapter number as category prefix for context
        num = _handbook_chapter_num(slug)
        if num < 0:
            category = None
        else:
            category = f"Chapter {int(num)}"

        if add_source(cid, title=title, url=BASE + href,
                      order_by=order_by, category=category):
            print(f"  + [{order_by:2d}] {title}")
            added += 1
        else:
            print(f"  . [{order_by:2d}] {title} (exists)")

    print(f"  Total: {len(chapters)} chapters, {added} added")


# ---------------------------------------------------------------------------
# Come, Follow Me
# ---------------------------------------------------------------------------

CFM_MANUALS = [
    ('Come, Follow Me 2026 — Old Testament',
     '/study/manual/come-follow-me-for-home-and-church-old-testament-2026'),
]


def _cfm_category(slug):
    """Return a human-readable category label based on the slug pattern."""
    if re.match(r'^0{2,}', slug):          # 001-004 style
        return 'Introduction'
    m = re.match(r'^(\d+)(-|$)', slug)
    if not m:
        return None
    n = int(m.group(1))
    if m.group(2) == '-':
        return 'Overview'                  # 01-thoughts, 07-thoughts, etc.
    if n >= 53:
        return 'Appendix'
    return None                             # weekly lessons — no category needed


def scrape_cfm(name, index_path):
    print(f"\n  {name}")
    soup = fetch(index_path)

    pat = re.compile(r'^' + re.escape(index_path) + r'/([^/#]+)$')
    seen = set()
    slugs = []  # in DOM order
    for a in soup.find_all('a', href=True):
        h = href_base(a)
        m = pat.match(h)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        slugs.append((m.group(1), h))

    print(f"    {len(slugs)} entries — fetching titles...")

    cid, created = get_or_create_collection(name, name)
    print(f"    Collection {'created' if created else 'exists'}: {cid[:8]}")

    added = 0
    for order_by, (slug, href) in enumerate(slugs, start=1):
        try:
            page_soup = fetch(href)
        except Exception as e:
            print(f"    WARN: {slug}: {e}")
            continue

        h1 = page_soup.find('h1')
        title = clean(h1.get_text()) if h1 else slug.replace('-', ' ').title()
        category = _cfm_category(slug)

        if add_source(cid, title=title, url=BASE + href,
                      order_by=order_by, category=category):
            print(f"    + [{order_by:2d}] {title}")
            added += 1
        else:
            print(f"    . [{order_by:2d}] {title} (exists)")

    print(f"    Total: {len(slugs)} lessons, {added} added")


def scrape_all_cfm():
    print("\n=== COME, FOLLOW ME ===")
    for name, path in CFM_MANUALS:
        scrape_cfm(name, path)


# ---------------------------------------------------------------------------
# Hymns for Home and Church
# ---------------------------------------------------------------------------

HYMNS_INDEX = '/study/music/hymns-for-home-and-church'
HYMN_PAT = re.compile(r'^/study/music/hymns-for-home-and-church/([a-z][a-z0-9-]+)$')
HYMN_NUM_PAT = re.compile(r'^(\d{4})(.*)')


def scrape_hymns():
    print("\n=== HYMNS FOR HOME AND CHURCH ===")
    soup = fetch(HYMNS_INDEX)

    seen_slugs = set()
    hymns = []  # (order_by, href, title)

    for a in soup.find_all('a', href=True):
        h = href_base(a)
        if not HYMN_PAT.match(h):
            continue
        slug = h.split('/')[-1]
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)

        raw = clean(a.get_text())
        m = HYMN_NUM_PAT.match(raw)
        if m:
            num = int(m.group(1))
            title = m.group(2).strip()
        else:
            # No number prefix — use slug position as fallback order
            num = 9999
            title = raw

        if title:
            hymns.append((num, h, title))

    hymns.sort(key=lambda x: x[0])

    cid, created = get_or_create_collection(
        'Hymns for Home and Church',
        'New hymns and songs for home and church worship',
    )
    print(f"  Collection {'created' if created else 'exists'}: {cid[:8]}")

    added = 0
    for order_by, href, title in hymns:
        if add_source(cid, title=title, url=BASE + href, order_by=order_by):
            print(f"  + [{order_by}] {title}")
            added += 1

    print(f"  Total: {len(hymns)} hymns, {added} added")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Scrape Gospel Library into study_collection/study_source tables.')
    parser.add_argument('--gc-only', action='store_true',
                        help='Skip scriptures, only scrape General Conference')
    parser.add_argument('--scripture-only', action='store_true',
                        help='Skip GC, only scrape scriptures')
    parser.add_argument('--hymns-only', action='store_true',
                        help='Only scrape hymns')
    parser.add_argument('--handbook-only', action='store_true',
                        help='Only scrape General Handbook')
    parser.add_argument('--cfm-only', action='store_true',
                        help='Only scrape Come, Follow Me')
    parser.add_argument('--start-year', type=int, default=1971,
                        help='First GC year (default: 1971)')
    parser.add_argument('--end-year', type=int, default=None,
                        help='Last GC year (default: current year)')
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

        if args.hymns_only:
            scrape_hymns()
        elif args.handbook_only:
            scrape_handbook()
        elif args.cfm_only:
            scrape_all_cfm()
        else:
            if not args.gc_only:
                scrape_scriptures()
            if not args.scripture_only:
                scrape_gc(args.start_year, args.end_year)
            scrape_hymns()
            scrape_handbook()
            scrape_all_cfm()

    print("\nDone.")


if __name__ == '__main__':
    main()
