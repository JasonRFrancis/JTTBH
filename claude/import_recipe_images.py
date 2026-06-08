"""
Fetch images for recipes that have a source URL but no images yet.

Extracts the primary image from JSON-LD (Recipe schema) or og:image.
Falls back to Playwright on 403 responses.
Logs failures to claude/import_image_failures.json; retries those first on
subsequent runs.

Usage:
    python claude/import_recipe_images.py [--dry-run] [--user-id UUID] [--delay SECONDS]
"""

import json
import os
import re
import sys
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
}
DEFAULT_DELAY = 1.5
FAILURES_LOG = os.path.join(os.path.dirname(__file__), 'import_image_failures.json')


# ---------------------------------------------------------------------------
# Failure log helpers
# ---------------------------------------------------------------------------

def _load_failures() -> dict:
    if os.path.exists(FAILURES_LOG):
        with open(FAILURES_LOG) as f:
            return json.load(f)
    return {}


def _save_failures(failures: dict) -> None:
    with open(FAILURES_LOG, 'w') as f:
        json.dump(failures, f, indent=2)


# ---------------------------------------------------------------------------
# Image extraction
# ---------------------------------------------------------------------------

def _fetch_html(url: str) -> str:
    """Fetch page HTML, retrying with Playwright on 403."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        r.raise_for_status()
        return r.text
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 403:
            print('    (403 — retrying with Playwright)')
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=30000)
                content = page.content()
                browser.close()
            return content
        raise


def _image_from_jsonld(node: dict, page_url: str) -> str:
    raw = node.get('image')
    if not raw:
        return ''
    if isinstance(raw, list):
        raw = raw[0] if raw else None
    if isinstance(raw, dict):
        raw = raw.get('url', '')
    if not raw or not isinstance(raw, str):
        return ''
    url = raw.strip()
    if url.startswith('//'):
        url = 'https:' + url
    if not url.startswith('http'):
        url = urljoin(page_url, url)
    return url


def extract_image(page_url: str) -> str:
    """
    Return the primary image URL for a recipe page, or '' if none found.
    Checks JSON-LD Recipe schema first, then og:image.
    """
    html = _fetch_html(page_url)
    soup = BeautifulSoup(html, 'html.parser')

    # JSON-LD
    for script in soup.find_all('script', {'type': 'application/ld+json'}):
        try:
            raw = json.loads(script.string or '')
        except (json.JSONDecodeError, AttributeError):
            continue
        if isinstance(raw, dict) and '@graph' in raw:
            raw = raw['@graph']
        for node in (raw if isinstance(raw, list) else [raw]):
            if isinstance(node, dict) and node.get('@type') == 'Recipe':
                img = _image_from_jsonld(node, page_url)
                if img:
                    return img

    # og:image fallback
    og = soup.find('meta', {'property': 'og:image'})
    if og:
        url = (og.get('content') or '').strip()
        if url.startswith('//'):
            url = 'https:' + url
        if not url.startswith('http'):
            url = urljoin(page_url, url)
        return url

    return ''


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--user-id')
    parser.add_argument('--delay', type=float, default=DEFAULT_DELAY,
                        help=f'Seconds between requests (default {DEFAULT_DELAY})')
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    from app import create_app
    from app.models.recipe_model import RecipeModel
    from app.services.database import db_manager

    app = create_app()
    with app.app_context():
        user_id = args.user_id
        if not user_id:
            users = db_manager.execute_query("SELECT userID, username FROM user ORDER BY username", ())
            if not users:
                print('No users found.')
                sys.exit(1)
            print('Select user:')
            for i, u in enumerate(users):
                print(f"  {i+1}. {u['username']} ({u['userID']})")
            user_id = users[int(input('Enter number: ').strip()) - 1]['userID']

        # Recipes with source URL but no images
        rows = db_manager.execute_query("""
            SELECT r.recipeID, r.title, r.source
            FROM recipe r
            WHERE r.userID = %s
              AND r.id = (SELECT MAX(r2.id) FROM recipe r2 WHERE r2.recipeID = r.recipeID)
              AND r.title IS NOT NULL
              AND r.source IS NOT NULL AND r.source != ''
              AND r.source LIKE 'http%%'
              AND NOT EXISTS (
                  SELECT 1 FROM recipe_image ri WHERE ri.recipeID = r.recipeID AND ri.userID = %s
              )
            ORDER BY r.title
        """, (user_id, user_id))

        print(f'\n{len(rows)} recipes without images.')

        # Load failure log and prepend those to the front of the list
        failures = _load_failures()
        failed_ids = {f['recipeID'] for f in failures.values() if 'recipeID' in f}
        retry_rows = [r for r in rows if r['recipeID'] in failed_ids]
        normal_rows = [r for r in rows if r['recipeID'] not in failed_ids]
        rows = retry_rows + normal_rows

        if retry_rows:
            print(f'  Retrying {len(retry_rows)} previously failed recipes first.')

        found = skipped = err = 0

        for recipe in rows:
            rid = recipe['recipeID']
            label = (recipe['title'] or recipe['source'])[:65]
            source = recipe['source']

            print(f'  Fetching: {label}')
            try:
                img_url = extract_image(source)
                time.sleep(args.delay)

                if not img_url:
                    print(f'    (no image found)')
                    skipped += 1
                    failures.pop(source, None)
                    continue

                print(f'    → {img_url[:80]}')
                if not args.dry_run:
                    RecipeModel.add_image(rid, user_id, img_url)

                found += 1
                failures.pop(source, None)
                _save_failures(failures)

            except Exception as e:
                print(f'    ERROR: {e}')
                failures[source] = {
                    'recipeID': rid,
                    'title': recipe['title'],
                    'error': str(e),
                }
                _save_failures(failures)
                err += 1

        print(f'\n{"DRY RUN — " if args.dry_run else ""}Done.')
        print(f'  Images saved:  {found}')
        print(f'  No image:      {skipped}')
        print(f'  Errors:        {err}')
        if failures:
            print(f'  Failures logged to {FAILURES_LOG}')


if __name__ == '__main__':
    main()
