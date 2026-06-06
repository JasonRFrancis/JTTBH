"""
Import recipes from a Pinboard 'recipe' tag into JTTBH.

Fetches the public Pinboard JSON feed for jasonfrancis/recipe, then for each
URL attempts to extract recipe data via JSON-LD schema.org. Creates a full
recipe record on success or a stub (title + source) on failure.

Usage:
    python claude/import_pinboard_recipes.py [--dry-run] [--user-id UUID]

Options:
    --dry-run   Print what would be imported without writing to the database.
    --user-id   JTTBH userID to assign recipes to (prompts if omitted).
"""

import argparse
import json
import os
import re
import sys
import time
import uuid

import requests
from bs4 import BeautifulSoup

# Add project root to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

PINBOARD_FEED = 'https://feeds.pinboard.in/json/u:jasonfrancis/t:recipe/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
REQUEST_DELAY = 1.0  # seconds between recipe URL fetches


def main():
    parser = argparse.ArgumentParser(description='Import Pinboard recipes into JTTBH.')
    parser.add_argument('--dry-run', action='store_true', help='Print without writing to DB.')
    parser.add_argument('--user-id', help='JTTBH userID UUID.')
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    from app import create_app
    from app.models.recipe_model import RecipeModel

    app = create_app()
    with app.app_context():
        user_id = args.user_id
        if not user_id:
            from app.services.database import db_manager
            users = db_manager.execute_query("SELECT userID, username FROM user ORDER BY username", ())
            if not users:
                print('No users found in database.')
                sys.exit(1)
            print('Select user:')
            for i, u in enumerate(users):
                print(f"  {i+1}. {u['username']} ({u['userID']})")
            choice = input('Enter number: ').strip()
            user_id = users[int(choice) - 1]['userID']
            print(f"Using user: {user_id}")

        print(f"\nFetching Pinboard feed: {PINBOARD_FEED}")
        try:
            r = requests.get(PINBOARD_FEED, headers=HEADERS, timeout=15)
            r.raise_for_status()
            entries = r.json()
        except Exception as e:
            print(f"ERROR fetching Pinboard feed: {e}")
            sys.exit(1)

        print(f"Found {len(entries)} entries.\n")
        ok = stub = skip = err = 0

        for entry in entries:
            url = entry.get('u', '').strip()
            pb_title = entry.get('d', '').strip() or url

            if not url:
                print(f"  SKIP (no URL): {pb_title}")
                skip += 1
                continue

            if url.startswith('https://www.thekitchn.com'):
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(url)
                url = urlunparse(parsed._replace(query='', fragment=''))

            # Skip duplicates by source URL
            if not args.dry_run and RecipeModel.source_exists(user_id, url):
                print(f"  SKIP (exists): {pb_title}")
                skip += 1
                continue

            print(f"  Fetching: {pb_title[:60]}")
            try:
                data = _extract_recipe(url)
                time.sleep(REQUEST_DELAY)
            except Exception as e:
                print(f"    STUB (fetch error: {e})")
                data = {}
                err += 1

            recipe_data = {
                'title': data.get('title') or pb_title,
                'source': url,
                'type': data.get('type', ''),
                'servings': data.get('servings', ''),
                'prep_time': data.get('prep_time', ''),
                'cook_time': data.get('cook_time', ''),
                'ingredients': data.get('ingredients', []),
                'directions': data.get('directions', []),
                'notes': '',
            }

            has_content = bool(data.get('ingredients') or data.get('directions'))
            status = 'OK  ' if has_content else 'STUB'

            if has_content:
                ok += 1
            else:
                stub += 1

            print(f"    {status}: {recipe_data['title'][:60]}")
            if data.get('ingredients'):
                print(f"         {len(data['ingredients'])} ingredients, {len(data.get('directions', []))} steps")

            if not args.dry_run:
                RecipeModel.create_recipe(user_id, recipe_data)

        print(f"\n{'DRY RUN — ' if args.dry_run else ''}Done. OK={ok}  STUB={stub}  SKIP={skip}  ERR={err}")


def _fetch_html(url: str) -> str:
    """Fetch URL, falling back to Playwright on 403."""
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


def _extract_recipe(url: str) -> dict:
    html = _fetch_html(url)
    soup = BeautifulSoup(html, 'html.parser')

    for script in soup.find_all('script', {'type': 'application/ld+json'}):
        try:
            raw = json.loads(script.string or '')
        except (json.JSONDecodeError, AttributeError):
            continue
        if isinstance(raw, dict) and '@graph' in raw:
            raw = raw['@graph']
        candidates = raw if isinstance(raw, list) else [raw]
        for node in candidates:
            if isinstance(node, dict) and node.get('@type') == 'Recipe':
                return _parse_jsonld(node)

    result = {}
    og = soup.find('meta', {'property': 'og:title'})
    if og:
        result['title'] = og.get('content', '').strip()
    return result


def _parse_jsonld(data: dict) -> dict:
    result = {'title': (data.get('name') or '').strip()}

    yield_val = data.get('recipeYield')
    if yield_val:
        if isinstance(yield_val, list):
            yield_val = yield_val[0] if yield_val else ''
        result['servings'] = str(yield_val).strip()

    if data.get('prepTime'):
        result['prep_time'] = _iso_duration(data['prepTime'])
    if data.get('cookTime'):
        result['cook_time'] = _iso_duration(data['cookTime'])

    raw_ing = data.get('recipeIngredient')
    if raw_ing:
        result['ingredients'] = [
            {'amount': '', 'unit': '', 'item': str(i).strip(), 'note': ''}
            for i in raw_ing if str(i).strip()
        ]

    raw_instr = data.get('recipeInstructions')
    if raw_instr:
        directions = []
        if isinstance(raw_instr, str):
            directions = [raw_instr.strip()]
        elif isinstance(raw_instr, list):
            for step in raw_instr:
                if isinstance(step, str):
                    directions.append(step.strip())
                elif isinstance(step, dict):
                    directions.append((step.get('text') or '').strip())
        result['directions'] = [d for d in directions if d]

    cat = data.get('recipeCategory')
    if cat:
        if isinstance(cat, list):
            cat = cat[0] if cat else ''
        result['type'] = str(cat).strip()

    return result


def _iso_duration(s: str) -> str:
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', str(s))
    if not m:
        return str(s)
    h, mins = m.group(1), m.group(2)
    parts = []
    if h:
        parts.append(f'{h}h')
    if mins:
        parts.append(f'{mins}m')
    return ' '.join(parts) or str(s)


if __name__ == '__main__':
    main()
