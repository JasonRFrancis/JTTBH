"""
Import recipes from Pinboard into JTTBH.

Uses the authenticated Pinboard API to fetch all bookmarks under two tags:
  recipe  — each URL is a recipe page; imported directly.
  recipes — each URL is a roundup/index page; recipe links are extracted
             from the page content and queued for import.

URL extraction uses JSON-LD schema.org first, with Playwright as fallback
for sites that return 403 to plain requests.

Usage:
    python claude/import_pinboard_recipes.py [--dry-run] [--user-id UUID] [--api-token USER:TOKEN]

Options:
    --dry-run     Print what would be imported without writing to the database.
    --user-id     JTTBH userID UUID (prompts if omitted).
    --api-token   Pinboard API token (USER:TOKEN from pinboard.in/settings/password).
                  Falls back to PINBOARD_API_TOKEN env var, then prompts.
"""

import argparse
import json
import os
import re
import sys
import time
from urllib.parse import urlparse, urlunparse, urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

PINBOARD_API = 'https://api.pinboard.in/v1/posts/all'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
REQUEST_DELAY = 1.0

# Domains to skip when extracting recipe links from roundup pages
_SKIP_DOMAINS = {
    'twitter.com', 'x.com', 'facebook.com', 'instagram.com', 'pinterest.com',
    'youtube.com', 'tiktok.com', 'reddit.com', 'amazon.com', 'pinboard.in',
    'bit.ly', 'ow.ly', 'mailto:',
}

# File extensions to skip when extracting recipe links
_SKIP_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.zip', '.mp4', '.mp3', '.svg'}


def main():
    parser = argparse.ArgumentParser(description='Import Pinboard recipes into JTTBH.')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--user-id')
    parser.add_argument('--api-token', help='Pinboard API token (USER:TOKEN)')
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    from app import create_app
    from app.models.recipe_model import RecipeModel

    app = create_app()
    with app.app_context():
        # Resolve user
        user_id = args.user_id
        if not user_id:
            from app.services.database import db_manager
            users = db_manager.execute_query("SELECT userID, username FROM user ORDER BY username", ())
            if not users:
                print('No users found.')
                sys.exit(1)
            print('Select user:')
            for i, u in enumerate(users):
                print(f"  {i+1}. {u['username']} ({u['userID']})")
            user_id = users[int(input('Enter number: ').strip()) - 1]['userID']

        # Resolve API token
        api_token = args.api_token or os.environ.get('PINBOARD_API_TOKEN', '')
        if not api_token:
            api_token = input('Pinboard API token (USER:TOKEN from pinboard.in/settings/password): ').strip()

        # ----------------------------------------------------------------
        # Step 1: fetch both tags from Pinboard API
        # ----------------------------------------------------------------
        print('\nFetching Pinboard bookmarks...')
        recipe_entries  = _fetch_pinboard_tag(api_token, 'recipe')
        recipes_entries = _fetch_pinboard_tag(api_token, 'recipes')
        print(f'  recipe tag:  {len(recipe_entries)} bookmarks')
        print(f'  recipes tag: {len(recipes_entries)} bookmarks')

        # ----------------------------------------------------------------
        # Step 2: build URL queue
        # recipe entries → direct recipe URLs
        # recipes entries → fetch each page, extract recipe links within
        # ----------------------------------------------------------------
        queue = {}  # url -> pinboard title (may be empty for extracted links)

        for entry in recipe_entries:
            url = _normalize_url(entry.get('href', ''))
            if url:
                queue[url] = entry.get('description', '') or url

        print(f'\nExpanding {len(recipes_entries)} "recipes" pages...')
        for entry in recipes_entries:
            page_url = _normalize_url(entry.get('href', ''))
            if not page_url:
                continue
            pb_title = entry.get('description', page_url)
            print(f'  Scanning: {pb_title[:70]}')
            try:
                links = _extract_recipe_links(page_url)
                new = [l for l in links if l not in queue]
                for link in new:
                    queue[link] = ''
                print(f'    → {len(links)} links found, {len(new)} new')
                time.sleep(0.5)
            except Exception as e:
                print(f'    ERROR: {e}')

        print(f'\nTotal unique recipe URLs to process: {len(queue)}')
        if args.dry_run:
            print('(dry-run: skipping DB duplicate check)\n')

        # ----------------------------------------------------------------
        # Step 3: process each URL
        # ----------------------------------------------------------------
        ok = stub = skip = err = 0

        for url, pb_title in queue.items():
            if not args.dry_run and RecipeModel.source_exists(user_id, url):
                print(f'  SKIP (exists): {(pb_title or url)[:60]}')
                skip += 1
                continue

            label = (pb_title or url)[:60]
            print(f'  Fetching: {label}')
            try:
                data = _extract_recipe(url)
                time.sleep(REQUEST_DELAY)
            except Exception as e:
                print(f'    STUB (fetch error: {e})')
                data = {}
                err += 1

            recipe_data = {
                'title':       data.get('title') or pb_title or url,
                'source':      url,
                'type':        data.get('type', ''),
                'servings':    data.get('servings', ''),
                'prep_time':   data.get('prep_time', ''),
                'cook_time':   data.get('cook_time', ''),
                'ingredients': data.get('ingredients', []),
                'directions':  data.get('directions', []),
                'notes':       '',
            }

            has_content = bool(data.get('ingredients') or data.get('directions'))
            if has_content:
                ok += 1
                print(f'    OK  : {recipe_data["title"][:60]}  ({len(data.get("ingredients", []))} ing, {len(data.get("directions", []))} steps)')
            else:
                stub += 1
                print(f'    STUB: {recipe_data["title"][:60]}')

            if not args.dry_run:
                RecipeModel.create_recipe(user_id, recipe_data)

        print(f'\n{"DRY RUN — " if args.dry_run else ""}Done.  OK={ok}  STUB={stub}  SKIP={skip}  ERR={err}')


# ---------------------------------------------------------------------------
# Pinboard API
# ---------------------------------------------------------------------------

def _fetch_pinboard_tag(api_token: str, tag: str) -> list[dict]:
    r = requests.get(PINBOARD_API, params={
        'auth_token': api_token,
        'tag': tag,
        'format': 'json',
    }, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def _normalize_url(url: str) -> str:
    url = (url or '').strip()
    if not url.startswith('http'):
        return ''
    parsed = urlparse(url)
    # Strip query string from thekitchn.com (tracking noise)
    if 'thekitchn.com' in parsed.netloc:
        parsed = parsed._replace(query='', fragment='')
    else:
        parsed = parsed._replace(fragment='')
    return urlunparse(parsed)


def _is_skip_url(url: str) -> bool:
    parsed = urlparse(url)
    netloc = parsed.netloc.lower().lstrip('www.')
    if any(netloc == d or netloc.endswith('.' + d) for d in _SKIP_DOMAINS):
        return True
    path = parsed.path.lower()
    if not path or path == '/':
        return True
    last_segment = path.rsplit('/', 1)[-1]
    if '.' in last_segment:
        ext = '.' + last_segment.rsplit('.', 1)[-1]
        if ext in _SKIP_EXTENSIONS:
            return True
    return False


# ---------------------------------------------------------------------------
# Recipe link extraction (for "recipes" roundup pages)
# ---------------------------------------------------------------------------

def _extract_recipe_links(page_url: str) -> list[str]:
    """Fetch a roundup page and return URLs that could be individual recipes."""
    html = _fetch_html(page_url)
    soup = BeautifulSoup(html, 'html.parser')

    # Prefer main content areas to avoid nav/footer noise
    content = (
        soup.find('article') or
        soup.find('main') or
        soup.find(attrs={'role': 'main'}) or
        soup.find('div', id=re.compile(r'content|main', re.I)) or
        soup.body
    )
    if not content:
        return []

    seen = set()
    results = []
    for a in content.find_all('a', href=True):
        raw = a['href'].strip()
        if not raw or raw.startswith('#') or raw.startswith('javascript'):
            continue
        if not raw.startswith('http'):
            raw = urljoin(page_url, raw)
        url = _normalize_url(raw)
        if not url or url in seen or url == page_url or _is_skip_url(url):
            continue
        seen.add(url)
        results.append(url)

    return results


# ---------------------------------------------------------------------------
# Recipe data extraction (JSON-LD → Open Graph fallback)
# ---------------------------------------------------------------------------

def _fetch_html(url: str) -> str:
    """Fetch URL content, falling back to Playwright on 403."""
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
