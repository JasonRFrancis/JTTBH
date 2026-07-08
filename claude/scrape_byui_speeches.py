#!/usr/bin/env python3
"""
Scrape byui.edu/speeches for General Conference speakers.

Paginates the site's speech archive (search?p=N, sorted newest-first),
keeping only talks whose speaker also appears in the GC collections, and
adds them to a single "BYU-Idaho Speeches" collection (title, URL, date as
subtitle, category, MP3 audio URL where available, author = canonical GC
name). Safe to re-run — skips talks already present (by URL).

Usage:
    python3 claude/scrape_byui_speeches.py
    python3 claude/scrape_byui_speeches.py --dry-run   # show matches only
"""

import argparse
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.services.database import db_manager

import scrape_byu_speeches as byu
from scrape_byu_speeches import (
    fetch, parse_gc_name, meaningful_first, get_gc_authors,
    get_or_create_collection, source_exists, add_source, parse_date,
)

BYUI = 'https://www.byui.edu'

TITLES = {'elder', 'president', 'sister', 'brother', 'bishop'}


# ---------------------------------------------------------------------------
# Speaker matching (reuses scrape_byu_speeches's last-name + first-4-char rule)
# ---------------------------------------------------------------------------

def strip_title(name):
    """'Elder Mark A. Bragg' -> 'Mark A. Bragg'"""
    tokens = name.split()
    while tokens and tokens[0].rstrip('.').lower() in TITLES:
        tokens = tokens[1:]
    return ' '.join(tokens)


def build_gc_index(gc_authors):
    idx = defaultdict(list)
    for name in gc_authors:
        last, first = parse_gc_name(name)
        idx[last].append((first, name))
    return idx


def middle_initial(name):
    """
    'Henry B. Eyring' -> 'b'; 'Dallin H. Oaks' -> 'h'; 'Kriss Pond' -> None.
    Distinguishes people who share a first + last name (e.g. Henry B. Eyring
    the apostle vs. his son Henry J. Eyring, a BYU-Idaho president) via the
    token that isn't the last name or the meaningful first name.
    """
    tokens = name.strip().split()
    if len(tokens) < 3:
        return None
    first = meaningful_first(' '.join(tokens[:-1]))
    for tok in tokens[:-1]:
        clean = tok.rstrip('.').lower()
        if clean != first and len(clean) == 1:
            return clean
    return None


def match_gc_author(display_name, gc_index):
    """
    'Elder Gérald & Sister Valérie Caussé' -> 'Gérald Caussé' if that name is
    a GC speaker, else None. Handles joint talks by checking each name; a
    bare first name (e.g. 'Gérald' before the '&') borrows the surname from
    the other half, since joint credits usually share one surname.
    """
    parts = [strip_title(p.strip()) for p in re.split(r'\s*&\s*', display_name)]
    parts = [p for p in parts if p]
    shared_surname = next((p.split()[-1] for p in reversed(parts) if len(p.split()) >= 2), None)

    for part in parts:
        if len(part.split()) == 1 and shared_surname:
            part = f'{part} {shared_surname}'
        last, first = parse_gc_name(part)
        part_mi = middle_initial(part)
        for gc_first, gc_name in gc_index.get(last, []):
            key = first[:4] if len(first) >= 3 else first
            gc_key = gc_first[:4] if len(gc_first) >= 3 else gc_first
            if not (key and gc_key and key == gc_key):
                continue
            gc_mi = middle_initial(gc_name)
            if part_mi and gc_mi and part_mi != gc_mi:
                continue  # e.g. Henry B. Eyring vs. Henry J. Eyring
            return gc_name
    return None


# ---------------------------------------------------------------------------
# Listing / talk scraping
# ---------------------------------------------------------------------------

def scrape_search_page(page_num):
    """Return (list of talk dicts, total card count including 'Upcoming')."""
    soup = fetch(f'{BYUI}/speeches/search?p={page_num}')
    cards = soup.find_all('div', class_='PromoSpeechCard')

    items = []
    for card in cards:
        cat = card.find(class_='PromoSpeechCard-category')
        title = card.find(class_='PromoSpeechCard-title')
        author = card.find(class_='PromoSpeechCard-authorName')
        date = card.find(class_='PromoSpeechCard-date')
        if not (cat and title and author and date):
            continue

        cat_text = cat.get_text(strip=True)
        if cat_text.lower().startswith('upcoming'):
            continue

        a = title.find('a', href=True)
        if not a:
            continue
        if '/secure/' in a['href']:
            continue  # requires CES login; not publicly reachable

        items.append({
            'category': cat_text,
            'title': a.get_text(strip=True),
            'url': a['href'],
            'author_display': author.get_text(strip=True),
            'date_str': date.get_text(strip=True),
        })

    return items, len(cards)


def scrape_talk_audio(url):
    """MP3 URL from a talk's detail page, or None."""
    soup = fetch(url)
    audio = soup.find('audio')
    if audio:
        source = audio.find('source')
        if source and source.get('src'):
            return source['src']
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

MAX_PAGES = 500  # safety cap; archive is ~130 pages as of 2026


def run_import(dry_run=False):
    print("Loading GC speakers from DB...")
    gc_authors = get_gc_authors()
    gc_index = build_gc_index(gc_authors)
    print(f"  {len(gc_authors)} unique GC speakers")

    cid = None
    if not dry_run:
        cid, _ = get_or_create_collection(
            'BYU-Idaho Speeches',
            'Devotional, forum, and commencement addresses from BYU-Idaho. '
            'Filter by author to subscribe to talks by a specific speaker.')

    total_matched = 0
    total_added = 0
    page = 1
    prev_urls = None
    while page <= MAX_PAGES:
        items, card_count = scrape_search_page(page)
        if card_count == 0:
            break
        # Past the last real page, the site re-serves the same page instead
        # of an empty one — stop once a page repeats verbatim.
        urls = tuple(i['url'] for i in items)
        if urls == prev_urls:
            break
        prev_urls = urls

        page_added = 0
        for item in items:
            gc_name = match_gc_author(item['author_display'], gc_index)
            if not gc_name:
                continue
            total_matched += 1

            if dry_run:
                print(f"  p{page}: {item['author_display']:35s} -> {gc_name:25s} "
                      f"{item['title']} ({item['date_str']})")
                continue

            if source_exists(cid, item['url']):
                continue

            try:
                audio_url = scrape_talk_audio(item['url'])
            except Exception as e:
                print(f"  ERROR fetching {item['url']}: {e}")
                audio_url = None

            order_by, _ = parse_date(item['date_str'])
            if add_source(cid, title=item['title'], url=item['url'],
                          order_by=order_by, subtitle=item['date_str'] or None,
                          audio_url=audio_url, author=gc_name,
                          category=item['category']):
                page_added += 1

        if page_added:
            print(f"  page {page}: {page_added} added")
        total_added += page_added
        page += 1

    print(f"\nDone. {total_matched} GC-matched talks found on site, "
          f"{total_added} new sources added.")
    return total_added


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
        byu.ADMIN_USER_ID = row['userID']
        print(f"Admin: {byu.ADMIN_USER_ID[:8]}...")

        run_import(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
