#!/usr/bin/env python3
"""
Check "Hymns for Home and Church" for newly published hymns and add them,
with audio pointing at the "Vocal (Choir)" track.

Run from project root:
    python3 claude/update_hymns.py
    python3 claude/update_hymns.py --verify   # sanity-check audio scraping against a known hymn
"""

import asyncio
import os
import re
import sys
import uuid

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.services.database import db_manager

BASE = 'https://www.churchofjesuschrist.org'
HYMNS_INDEX = '/study/music/hymns-for-home-and-church'
HYMN_PAT = re.compile(r'^/study/music/hymns-for-home-and-church/([a-z][a-z0-9-]+)$')
HYMN_NUM_PAT = re.compile(r'^(\d{4})(.*)')
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}
PREFERRED_TRACKS = ['Vocal (Choir)', 'Vocal (Congregation)', 'Vocal (Children)']


def clean(s):
    if not s:
        return ''
    s = s.replace('Â ', ' ').replace(' ', ' ')
    return ' '.join(s.split()).strip()


def fetch_index():
    """Scrape the hymn index page. Returns [(num, href, title), ...] sorted by num."""
    url = BASE + HYMNS_INDEX + '?lang=eng'
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser', from_encoding='utf-8')

    seen, hymns = set(), []
    for a in soup.find_all('a', href=True):
        h = a['href'].split('?')[0].rstrip('/')
        if not HYMN_PAT.match(h):
            continue
        slug = h.split('/')[-1]
        if slug in seen:
            continue
        seen.add(slug)
        raw = clean(a.get_text())
        m = HYMN_NUM_PAT.match(raw)
        num, title = (int(m.group(1)), m.group(2).strip()) if m else (9999, raw)
        if title:
            hymns.append((num, h, title))
    hymns.sort(key=lambda x: x[0])
    return hymns


async def fetch_track_audio_url(page, url):
    """Open a hymn page's audio player and return the mp3 URL for the best
    available vocal track (Choir preferred, Congregation as fallback), or
    the player's default track if neither is offered."""
    await page.goto(url, wait_until='domcontentloaded')
    await page.get_by_test_id('floating-audio-button').click(timeout=10000)
    await page.get_by_role('button', name='Settings').click(timeout=10000)

    combo = page.get_by_label('Audio Type')
    options = await combo.evaluate("el => Array.from(el.options).map(o => o.value)")

    track = next((t for t in PREFERRED_TRACKS if t in options), None)
    if track:
        await combo.select_option(track)
        await page.wait_for_timeout(800)
    else:
        print(f"    WARN: no vocal track available ({options}); using default")

    src = await page.evaluate("document.querySelector('audio')?.currentSrc || null")
    return src


async def verify():
    """One-off sanity check: known hymn's stored audio_url should match what
    the scraper fetches live for the Choir track."""
    app = create_app()
    with app.app_context():
        row = db_manager.execute_one(
            "SELECT audio_url FROM study_source WHERE title='Long Ago, Within a Garden' "
            "AND title IS NOT NULL LIMIT 1", ())
    assert row, "reference hymn not found in DB"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        url = BASE + '/study/music/hymns-for-home-and-church/long-ago-within-a-garden?lang=eng'
        fetched = await fetch_track_audio_url(page, url)
        await browser.close()

    assert fetched == row['audio_url'], f"mismatch: DB={row['audio_url']} fetched={fetched}"
    print("OK: fetched Choir audio URL matches stored value.")


async def main():
    app = create_app()
    with app.app_context():
        admin = db_manager.execute_one("SELECT userID FROM `user` WHERE admin = 1 LIMIT 1", ())
        if not admin:
            print("ERROR: no admin user found")
            sys.exit(1)
        admin_id = admin['userID']

        collection = db_manager.execute_one("""
            SELECT sc.collectionID FROM study_collection sc
            WHERE sc.name = 'Hymns for Home and Church' AND sc.name IS NOT NULL
              AND sc.id = (SELECT MAX(s2.id) FROM study_collection s2 WHERE s2.collectionID = sc.collectionID)
            LIMIT 1
        """, ())
        if not collection:
            print("ERROR: 'Hymns for Home and Church' collection not found — run "
                  "scrape_gospel_library.py --hymns-only first")
            sys.exit(1)
        cid = collection['collectionID']

        existing_urls = {
            r['url'] for r in db_manager.execute_query(
                "SELECT url FROM study_source WHERE collectionID=%s AND title IS NOT NULL", (cid,))
        }

        hymns = fetch_index()
        new_hymns = [(num, h, title) for num, h, title in hymns if (BASE + h) not in existing_urls]

        print(f"Found {len(hymns)} hymns on the index page, {len(new_hymns)} new.")
        if not new_hymns:
            print("Done.")
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            for num, href, title in new_hymns:
                full_url = BASE + href + '?lang=eng'
                try:
                    audio_url = await fetch_track_audio_url(page, full_url)
                except Exception as e:
                    print(f"  WARN: {title}: could not fetch audio ({e})")
                    audio_url = None

                db_manager.execute_insert("""
                    INSERT INTO study_source
                      (sourceID, collectionID, userID, title, url, audio_url, order_by, created, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                """, (str(uuid.uuid4()), cid, admin_id, title, BASE + href, audio_url, num, admin_id))
                print(f"  + [{num}] {title}  audio={'yes' if audio_url else 'MISSING'}")
            await browser.close()

    print("Done.")


if __name__ == '__main__':
    if '--verify' in sys.argv:
        asyncio.run(verify())
    else:
        asyncio.run(main())
