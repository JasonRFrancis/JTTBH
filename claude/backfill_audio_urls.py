#!/usr/bin/env python3
"""
Backfill audio_url on study_source rows using Playwright.

Audio is available for:
  - All scripture chapters (all standard works)
  - General Conference 2018 and later

Usage (from project root):
    python3 claude/backfill_audio_urls.py
    python3 claude/backfill_audio_urls.py --concurrency 8
    python3 claude/backfill_audio_urls.py --limit 50        # test run
    python3 claude/backfill_audio_urls.py --collection-like "Book of Mormon"
"""

import argparse
import asyncio
import os
import re
import sys
from datetime import datetime

from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.services.database import db_manager

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')


# ---------------------------------------------------------------------------
# Database helpers (all called within app_context in main)
# ---------------------------------------------------------------------------

def get_sources(collection_like=None, limit=None):
    """Return sources that need audio_url filled in."""
    sql = """
        SELECT ss.id, ss.sourceID, ss.url, sc.name AS collection_name
        FROM study_source ss
        JOIN study_collection sc ON sc.collectionID = ss.collectionID
        WHERE ss.title IS NOT NULL
          AND (ss.audio_url IS NULL OR ss.audio_url = '')
          AND ss.url IS NOT NULL
          AND ss.url != ''
          AND sc.id = (SELECT MAX(sc2.id) FROM study_collection sc2
                       WHERE sc2.collectionID = sc.collectionID)
          AND sc.name IS NOT NULL
    """
    params = []
    if collection_like:
        sql += " AND sc.name LIKE %s"
        params.append(f'%{collection_like}%')
    sql += " ORDER BY sc.name, ss.order_by"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return db_manager.execute_query(sql, tuple(params))


def mark_no_audio(source_id):
    db_manager.execute_update(
        "UPDATE study_source SET audio_url = 'none' WHERE id = %s",
        (source_id,))


def save_audio_url(source_id, audio_url):
    db_manager.execute_update(
        "UPDATE study_source SET audio_url = %s WHERE id = %s",
        (audio_url, source_id))


def should_have_audio(collection_name):
    """Skip GC conferences before 2018 — they have no audio player."""
    m = re.match(r'General Conference — \w+ (\d{4})$', collection_name)
    if m:
        return int(m.group(1)) >= 2018
    return True  # scriptures always have audio


# ---------------------------------------------------------------------------
# Playwright audio extraction
# ---------------------------------------------------------------------------

async def get_audio_url(page, url):
    """
    Load url, click Audio Player, return the MP3 URL or None.
    Returns (audio_url_or_None, status_string).
    """
    try:
        await page.goto(url + '?lang=eng', wait_until='load', timeout=25000)
        await page.wait_for_timeout(1200)

        btn = await page.query_selector('button[aria-label="Audio Player"]')
        if not btn:
            return None, 'no_button'

        await btn.click()

        try:
            await page.wait_for_selector(
                'source[src$=".mp3"], source[src*=".mp3"]',
                state='attached', timeout=15000)
        except Exception:
            return None, 'no_source_after_click'

        src = await page.evaluate("""() => {
            const el = document.querySelector('source[src$=".mp3"], source[src*=".mp3"]');
            return el ? (el.src || el.getAttribute('src')) : null;
        }""")
        return src or None, 'ok'

    except Exception as e:
        return None, f'error:{str(e)[:60]}'


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

async def worker(worker_id, queue, browser, results, app_context):
    context = await browser.new_context(user_agent=UA)
    page = await context.new_page()

    while True:
        try:
            item = queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        row_id = item['id']
        url = item['url']
        collection = item['collection_name']

        audio_url, status = await get_audio_url(page, url)

        # Write to DB
        with app_context:
            if audio_url:
                save_audio_url(row_id, audio_url)
            elif status == 'no_button':
                mark_no_audio(row_id)
            # else: transient error, leave NULL to retry later

        results.append((url, audio_url, status))

        short_url = url.split('/')[-1]
        if audio_url:
            print(f"  [W{worker_id}] + {short_url[:50]:50s}  {audio_url[-35:]}")
        else:
            print(f"  [W{worker_id}] - {short_url[:50]:50s}  ({status})")

        queue.task_done()

    await page.close()
    await context.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run(args, app):
    with app.app_context():
        sources = get_sources(args.collection_like, args.limit)

    # Filter out collections known to have no audio
    eligible = [s for s in sources if should_have_audio(s['collection_name'])]
    skipped  = len(sources) - len(eligible)
    print(f"Sources needing audio_url: {len(sources)}")
    print(f"Skipped (pre-2018 GC, no audio): {skipped}")
    print(f"To process: {len(eligible)}")
    print(f"Concurrency: {args.concurrency}")
    if not eligible:
        print("Nothing to do.")
        return

    queue = asyncio.Queue()
    for s in eligible:
        await queue.put(s)

    results = []
    start = datetime.now()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        # Each worker needs its own app_context for DB writes.
        # Pass the app object and push context per write in worker.
        # Actually we'll just use a lock + single context for DB.
        # Simpler: collect (id, url) results and batch-write in main.

        # Revised: workers collect results, main thread writes to DB.
        worker_results = []
        lock = asyncio.Lock()

        async def safe_worker(wid):
            context = await browser.new_context(user_agent=UA)
            page = await context.new_page()
            while True:
                try:
                    item = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                row_id = item['id']
                url = item['url']
                audio_url, status = await get_audio_url(page, url)
                async with lock:
                    worker_results.append((row_id, url, audio_url, status))
                    done = len(worker_results)
                    short = url.split('/')[-1]
                    if audio_url:
                        print(f"  [{done:4d}/{len(eligible)}] + {short[:55]:55s}  {audio_url[-35:]}")
                    else:
                        print(f"  [{done:4d}/{len(eligible)}] - {short[:55]:55s}  ({status})")
                queue.task_done()
            await page.close()
            await context.close()

        workers = [asyncio.create_task(safe_worker(i+1))
                   for i in range(min(args.concurrency, len(eligible)))]
        await asyncio.gather(*workers)
        await browser.close()

    # Batch write to DB
    print(f"\nWriting results to database...")
    with app.app_context():
        ok = no_btn = errors = 0
        for row_id, url, audio_url, status in worker_results:
            if audio_url:
                save_audio_url(row_id, audio_url)
                ok += 1
            elif status == 'no_button':
                mark_no_audio(row_id)
                no_btn += 1
            else:
                errors += 1

    elapsed = (datetime.now() - start).seconds
    print(f"\nDone in {elapsed}s: {ok} audio URLs saved, {no_btn} marked no-audio, {errors} errors")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--concurrency', type=int, default=6,
                        help='Number of parallel browser pages (default 6)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Max sources to process (for test runs)')
    parser.add_argument('--collection-like', default=None,
                        help='Filter by collection name substring')
    args = parser.parse_args()

    app = create_app()
    asyncio.run(run(args, app))


if __name__ == '__main__':
    main()
