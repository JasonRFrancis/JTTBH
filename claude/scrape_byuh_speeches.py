#!/usr/bin/env python3
"""
Scrape speeches.byuh.edu (BYU-Hawaii) for General Conference speakers.

For every speaker who appears in both the GC collections and the BYUH
speaker directory (speeches.byuh.edu/speakers), adds their talks to a single
"BYU-Hawaii Speeches" collection (title, URL, date as subtitle, author =
canonical GC name). BYUH speeches don't offer downloadable audio — talks are
embedded YouTube videos, not enclosure-friendly files — so audio_url is
always None. Safe to re-run — skips talks already present (by URL).

A speaker's own page can also list a co-presenter's talk (e.g. a joint
devotional credited to a spouse), so each talk card's byline is matched
against the GC roster with scrape_byui_speeches.match_gc_author rather than
assumed to belong to the page's namesake.

Usage:
    python3 claude/scrape_byuh_speeches.py
    python3 claude/scrape_byuh_speeches.py --dry-run   # show matches only
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.services.database import db_manager

import scrape_byu_speeches as byu
from scrape_byu_speeches import (
    fetch, parse_gc_name, get_gc_authors,
    get_or_create_collection, add_source, parse_date,
)
from scrape_byui_speeches import build_gc_index, match_gc_author

BYUH = 'https://speeches.byuh.edu'


# ---------------------------------------------------------------------------
# Speaker directory
# ---------------------------------------------------------------------------

def load_byuh_speakers():
    """
    Return {speeches.byuh.edu URL: (last, first_meaningful, display_name, 0)}.

    The /speakers directory mixes in about.byuh.edu staff-bio links for
    people without a dedicated speeches page — those are skipped. The trailing
    0 is a dummy talk-count so this shape matches scrape_byu_speeches's
    (last, first, display, count) and its match_speakers() can be reused as-is.
    """
    soup = fetch(f'{BYUH}/speakers')
    speakers = {}
    for a in soup.find_all('a', class_='ListLinks-link', href=True):
        href = a['href']
        if not href.startswith(f'{BYUH}/'):
            continue
        display = a.get_text(strip=True)
        if not display:
            continue
        last, first = parse_gc_name(display)
        speakers[href] = (last, first, display, 0)
    return speakers


# ---------------------------------------------------------------------------
# Talk scraping
# ---------------------------------------------------------------------------

def scrape_speaker_talks(speaker_url, gc_name, gc_index):
    """
    Scrape talks from a BYUH speaker page, keeping only cards whose byline
    resolves (via match_gc_author) to *gc_name* — filters out co-presenters'
    talks that are cross-listed on this page.

    Returns list of (order_by_int, title, url, date_str).
    """
    soup = fetch(speaker_url)
    talks = []

    for card in soup.find_all('div', class_='PromoCardImageOnTop'):
        h3 = card.find('h3', class_='PromoCardImageOnTop-title')
        a = h3.find('a', href=True) if h3 else None
        if not a:
            continue

        author_div = card.find('div', class_='PromoCardImageOnTop-authorName')
        author_text = re.sub(r'^By\s*', '', author_div.get_text(strip=True)) if author_div else ''
        if match_gc_author(author_text, gc_index) != gc_name:
            continue

        title = a.get_text(strip=True)
        talk_url = a['href']

        date_div = card.find('div', class_='PromoCardImageOnTop-date')
        date_str = date_div.get_text(strip=True) if date_div else ''
        order_int, date_display = parse_date(date_str)

        talks.append((order_int, title, talk_url, date_display))

    talks.sort(key=lambda x: x[0])
    return talks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_import(dry_run=False):
    print("Loading GC speakers from DB...")
    gc_authors = get_gc_authors()
    gc_index = build_gc_index(gc_authors)
    print(f"  {len(gc_authors)} unique GC speakers")

    print("Loading BYU-Hawaii speaker directory...")
    byuh_speakers = load_byuh_speakers()
    print(f"  {len(byuh_speakers)} BYU-Hawaii speakers")

    matches = byu.match_speakers(gc_authors, byuh_speakers)
    print(f"\nMatched: {len(matches)} speakers\n")

    if dry_run:
        for gc_name, byuh_url, byuh_display, _count in matches:
            print(f"  {gc_name:40s}  {byuh_display}")
        return 0

    cid, _ = get_or_create_collection(
        'BYU-Hawaii Speeches',
        'Devotional addresses from BYU-Hawaii. '
        'Filter by author to subscribe to talks by a specific speaker.')

    total_sources = 0
    for i, (gc_name, byuh_url, byuh_display, _count) in enumerate(matches, 1):
        try:
            talks = scrape_speaker_talks(byuh_url, gc_name, gc_index)
        except Exception as e:
            print(f"  [{i:3d}/{len(matches)}] ERROR {gc_name}: {e}")
            continue

        added = 0
        for order_by, title, talk_url, date_str in talks:
            if add_source(cid, title=title, url=talk_url,
                          order_by=order_by, subtitle=date_str or None,
                          audio_url=None, author=gc_name):
                added += 1

        total_sources += added
        print(f"  [{i:3d}/{len(matches)}] {gc_name}: {len(talks)} talks — {added} added")

    print(f"\nDone. Total sources added: {total_sources}")
    return total_sources


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
