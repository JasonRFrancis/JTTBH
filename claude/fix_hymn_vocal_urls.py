#!/usr/bin/env python3
"""
Fix hymn audio URLs to use Vocal instead of Accompaniment.

The audio player on each hymn page defaults to Accompaniment.
Under Settings there's a <select> with options: Accompaniment,
Accompaniment (Guitar), Vocal, Vocal (Choir).
This script selects "Vocal" and captures the new MP3 URL.

Usage (from project root):
    python3 claude/fix_hymn_vocal_urls.py
    python3 claude/fix_hymn_vocal_urls.py --dry-run     # print, don't save
    python3 claude/fix_hymn_vocal_urls.py --limit 5     # test a handful
    python3 claude/fix_hymn_vocal_urls.py --concurrency 3
"""

import argparse
import asyncio
import os
import sys

from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.services.database import db_manager

COLLECTION_ID = '7b5e5b53-d699-4272-b801-c933d5648ce5'  # Hymns for Home and Church

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')


def get_hymn_sources(limit=None):
    sql = """
        SELECT id, sourceID, title, url
        FROM study_source
        WHERE collectionID = %s
          AND url IS NOT NULL AND url != ''
          AND title IS NOT NULL
        ORDER BY order_by
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    return db_manager.execute_query(sql, (COLLECTION_ID,))


def save_audio_url(row_id, audio_url):
    db_manager.execute_update(
        "UPDATE study_source SET audio_url = %s WHERE id = %s",
        (audio_url, row_id)
    )


async def get_vocal_url(page, url):
    """
    Navigate to a hymn page, open the audio player, open Settings,
    select "Vocal" from the Audio Type dropdown, and return the new MP3 URL.
    """
    try:
        await page.goto(url + '?lang=eng', wait_until='load', timeout=30000)
        await page.wait_for_timeout(1500)

        # 1. Open the audio player
        btn = await page.query_selector('button[aria-label="Audio Player"]')
        if not btn:
            return None, 'no_audio_button'
        await btn.click()
        await page.wait_for_timeout(1500)

        # 2. Wait for the initial (Accompaniment) source to load
        try:
            await page.wait_for_selector('source[src*=".mp3"]', state='attached', timeout=10000)
        except Exception:
            return None, 'no_initial_source'

        # 3. Open Settings to reveal the Audio Type <select>
        settings = await page.query_selector('button[aria-label="Settings"]')
        if not settings:
            return None, 'no_settings_button'
        await settings.click()
        await page.wait_for_timeout(800)

        # 4. Wait for and select "Vocal" from the Audio Type <select>
        # Look specifically for the select containing "Accompaniment" options
        try:
            await page.wait_for_selector('select', state='visible', timeout=10000)
        except Exception:
            return None, 'select_not_visible'

        # Find the audio-type select (it contains "Accompaniment" as an option)
        sel = await page.evaluate_handle("""() => {
            const selects = [...document.querySelectorAll('select')];
            return selects.find(s =>
                [...s.options].some(o => o.value === 'Accompaniment')
            ) || null;
        }""")
        if not sel or await sel.evaluate('el => !el') :
            return None, 'no_audio_type_select'

        await sel.scroll_into_view_if_needed()
        await page.wait_for_timeout(300)

        # Prefer plain "Vocal"; fall back to Choir or Children as available
        options = await sel.evaluate(
            'el => [...el.options].map(o => o.value)'
        )
        vocal_choice = next(
            (o for o in ['Vocal', 'Vocal (Choir)', 'Vocal (Children)'] if o in options),
            None
        )
        if not vocal_choice:
            return None, f'no_vocal_option (available: {options})'
        await sel.select_option(vocal_choice)

        await page.wait_for_timeout(2000)

        # 5. Read the new source URL
        src = await page.evaluate("""() => {
            const el = document.querySelector('source[src*=".mp3"]');
            return el ? (el.src || el.getAttribute('src')) : null;
        }""")

        if not src:
            return None, 'no_source_after_vocal_select'

        return src, 'ok'

    except Exception as e:
        return None, f'error:{str(e)[:100]}'


async def run_worker(wid, queue, browser, app, dry_run, results, lock):
    ctx = await browser.new_context(user_agent=UA)
    page = await ctx.new_page()

    while True:
        try:
            row = queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        vocal_url, status = await get_vocal_url(page, row['url'])

        async with lock:
            results.append((row, vocal_url, status))
            done = len(results)
            short = row['title'][:55]
            if vocal_url:
                print(f"  [{done:3d}] + {short:55s}  …{vocal_url[-45:]}")
            else:
                print(f"  [{done:3d}] - {short:55s}  ({status})")

        if vocal_url and not dry_run:
            with app.app_context():
                save_audio_url(row['id'], vocal_url)

        queue.task_done()

    await page.close()
    await ctx.close()


async def run(args, app):
    with app.app_context():
        sources = get_hymn_sources(args.limit)

    total = len(sources)
    print(f"Hymns to process: {total}")
    if args.dry_run:
        print("DRY RUN — no database changes will be made")
    print(f"Concurrency: {args.concurrency}\n")

    queue = asyncio.Queue()
    for s in sources:
        await queue.put(s)

    results = []
    lock = asyncio.Lock()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        workers = [
            asyncio.create_task(
                run_worker(i + 1, queue, browser, app, args.dry_run, results, lock)
            )
            for i in range(min(args.concurrency, total))
        ]
        await asyncio.gather(*workers)
        await browser.close()

    ok = sum(1 for _, url, _ in results if url)
    failed = total - ok
    print(f"\nDone: {ok} vocal URLs {'found (dry run)' if args.dry_run else 'saved'}, {failed} failed")

    if failed:
        print("\nFailed hymns:")
        for row, url, status in results:
            if not url:
                print(f"  {row['title']} — {status}")


def main():
    parser = argparse.ArgumentParser(description='Fix hymn audio URLs to Vocal version')
    parser.add_argument('--limit', type=int, default=None,
                        help='Process only N hymns (for testing)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print URLs but do not update the database')
    parser.add_argument('--concurrency', type=int, default=3,
                        help='Parallel browser pages (default 3)')
    args = parser.parse_args()

    app = create_app()
    asyncio.run(run(args, app))


if __name__ == '__main__':
    main()
