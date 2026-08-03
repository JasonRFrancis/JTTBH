#!/usr/bin/env python3
"""
Add "Preach My Gospel" as a study collection.
Populates study_collection and study_source tables.

Run from project root:
    python3 claude/add_preach_my_gospel.py
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright

from app import create_app
from app.services.database import db_manager

import scrape_gospel_library as sgl
from scrape_gospel_library import BASE, fetch, clean, href_base, get_or_create_collection, add_source

# Index is one level deep for most pages (…/preach-my-gospel-2023/03-chapter-1)
# but Chapter 3's lessons live one level deeper (…/04-chapter-3/06-chapter-3-intro).
# The leading number on the final path segment still gives correct document order
# across both levels (01, 02, 03, 04, 06, 07 … 11, 12, 13 … 21).
INDEX = '/study/manual/preach-my-gospel-2023'
PAGE_PAT = re.compile(r'^' + re.escape(INDEX) + r'/(?:[^/#]+/)?([^/#]+)$')
ORDER_PAT = re.compile(r'^(\d+)')


def get_audio_url(page, href):
    """Visit a page in a real browser and return its mp3 src, or None if it has no audio.

    The audio player is mounted client-side after page load, so this needs a
    browser rather than requests+BeautifulSoup (matches the approach used by
    the site's other audio backfill scripts).
    """
    page.goto(f'{BASE}{href}?lang=eng', wait_until='domcontentloaded')
    btn = page.locator('button[aria-label="Audio Player"]')
    try:
        btn.wait_for(state='attached', timeout=5000)
    except Exception:
        return None
    btn.click()
    src = page.locator('source[src$=".mp3"]')
    try:
        src.wait_for(state='attached', timeout=8000)
    except Exception:
        return None
    return src.get_attribute('src')


def scrape():
    print("\n=== PREACH MY GOSPEL ===")
    soup = fetch(INDEX)

    seen = set()
    pages = []  # (order_by, href)
    for a in soup.find_all('a', href=True):
        h = href_base(a)
        m = PAGE_PAT.match(h)
        if not m or h in seen:
            continue
        seen.add(h)
        om = ORDER_PAT.match(m.group(1))
        order_by = int(om.group(1)) if om else 999
        pages.append((order_by, h))

    pages.sort(key=lambda x: x[0])
    print(f"  Found {len(pages)} pages — fetching titles...")

    cid, created = get_or_create_collection(
        'Preach My Gospel',
        'Preach My Gospel: A Guide to Missionary Service',
    )
    print(f"  Collection {'created' if created else 'exists'}: {cid[:8]}")

    added = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        browser_page = browser.new_page()

        for order_by, href in pages:
            try:
                page_soup = fetch(href)
            except Exception as e:
                print(f"  WARN: {href}: {e}")
                continue

            h1 = page_soup.find('h1')
            title = clean(h1.get_text()) if h1 else href.split('/')[-1].replace('-', ' ').title()
            audio_url = get_audio_url(browser_page, href)

            if add_source(cid, title=title, url=BASE + href, order_by=order_by, audio_url=audio_url):
                audio_flag = '' if audio_url else ' (no audio)'
                print(f"  + [{order_by:2d}] {title}{audio_flag}")
                added += 1
            else:
                print(f"  . [{order_by:2d}] {title} (exists)")

        browser.close()

    print(f"  Total: {len(pages)} pages, {added} added")


def main():
    app = create_app()
    with app.app_context():
        row = db_manager.execute_one("SELECT userID FROM `user` WHERE admin = 1 LIMIT 1", ())
        if not row:
            print("ERROR: no admin user found in database")
            sys.exit(1)
        sgl.ADMIN_USER_ID = row['userID']
        print(f"Admin user: {sgl.ADMIN_USER_ID[:8]}...")
        scrape()

    print("\nDone.")


if __name__ == '__main__':
    main()
