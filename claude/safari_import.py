"""
safari_import.py — import Safari iCloud tabs or bookmarks into JTTBH.

Prerequisites
-------------
1. Full Disk Access granted to your terminal app:
   System Settings → Privacy & Security → Full Disk Access → add Terminal / iTerm2

2. IMPORT_API_KEY set in production .env (same value used here):
   Generate one with:  python3 -c "import secrets; print(secrets.token_hex(32))"

3. Env var (or hard-code below):
   export JTTBH_IMPORT_KEY=<your_key>

Usage — Tabs
------------
  # List available devices
  python3 claude/safari_import.py --list

  # Import tabs from a specific device (partial name match, case-insensitive)
  python3 claude/safari_import.py --device "iphone"

  # Import from all devices
  python3 claude/safari_import.py --all

  # Dry run (prints what would be imported without posting)
  python3 claude/safari_import.py --device "iphone" --dry-run

Usage — Bookmarks
-----------------
  # Import all bookmarks (Favorites bar + Bookmarks Menu; excludes Reading List)
  python3 claude/safari_import.py --bookmarks

  # Import only a specific folder (partial name match, case-insensitive)
  python3 claude/safari_import.py --bookmarks --folder "Apps"

  # Dry run
  python3 claude/safari_import.py --bookmarks --dry-run
"""

import argparse
import json
import os
import plistlib
import re
import shutil
import sqlite3
import sys
import tempfile
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Configuration — override with env vars or edit here
# ---------------------------------------------------------------------------

JTTBH_URL      = os.environ.get('JTTBH_URL',        'https://jttbh.com')
JTTBH_USERNAME = os.environ.get('JTTBH_USERNAME',   'jason')
JTTBH_API_KEY  = os.environ.get('JTTBH_IMPORT_KEY', '')

CLOUD_TABS_DB  = os.path.expanduser(
    '~/Library/Containers/com.apple.Safari/Data/Library/Safari/CloudTabs.db'
)
BOOKMARKS_PLIST = os.path.expanduser('~/Library/Safari/Bookmarks.plist')

# Top-level folder identifiers to skip when importing bookmarks
SKIP_FOLDERS = {'com.apple.ReadingList', 'History'}

_UNREAD_COUNT_RE = re.compile(r'^\(\d+\)\s*')

# ---------------------------------------------------------------------------
# Read CloudTabs.db (tabs)
# ---------------------------------------------------------------------------

def open_db() -> sqlite3.Connection:
    if not os.path.exists(CLOUD_TABS_DB):
        sys.exit(
            f'ERROR: {CLOUD_TABS_DB} not found.\n'
            'Make sure Safari is enabled for iCloud and iCloud Tabs is on.'
        )
    tmp = tempfile.mktemp(suffix='.db')
    shutil.copy2(CLOUD_TABS_DB, tmp)
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    return conn


def get_devices(conn: sqlite3.Connection) -> list[dict]:
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

    if 'cloud_tab_devices' in tables:
        rows = conn.execute("SELECT device_uuid, device_name FROM cloud_tab_devices").fetchall()
        return [{'uuid': r['device_uuid'], 'name': r['device_name']} for r in rows]

    if 'cloud_tabs' in tables:
        rows = conn.execute("SELECT DISTINCT device_uuid FROM cloud_tabs").fetchall()
        return [{'uuid': r['device_uuid'], 'name': r['device_uuid'][:8]} for r in rows]

    sys.exit('ERROR: Could not find device table in CloudTabs.db. Schema may have changed.')


def get_tabs(conn: sqlite3.Connection, device_uuids: list[str] | None) -> list[dict]:
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if 'cloud_tabs' not in tables:
        sys.exit('ERROR: cloud_tabs table not found in CloudTabs.db.')

    cols = {r[1] for r in conn.execute('PRAGMA table_info(cloud_tabs)').fetchall()}
    order_col = 'position_index' if 'position_index' in cols else 'rowid'

    if device_uuids:
        placeholders = ','.join('?' * len(device_uuids))
        rows = conn.execute(
            f'SELECT title, url FROM cloud_tabs WHERE device_uuid IN ({placeholders}) ORDER BY {order_col}',
            device_uuids,
        ).fetchall()
    else:
        rows = conn.execute(
            f'SELECT title, url FROM cloud_tabs ORDER BY {order_col}'
        ).fetchall()

    return [
        {'title': _UNREAD_COUNT_RE.sub('', r['title'] or r['url']), 'url': r['url']}
        for r in rows if r['url']
    ]


# ---------------------------------------------------------------------------
# Read Bookmarks.plist
# ---------------------------------------------------------------------------

def get_bookmarks(folder_filter: str | None) -> list[dict]:
    if not os.path.exists(BOOKMARKS_PLIST):
        sys.exit(f'ERROR: {BOOKMARKS_PLIST} not found.')

    with open(BOOKMARKS_PLIST, 'rb') as f:
        data = plistlib.load(f)

    results: list[dict] = []

    def walk(node: dict, inside_match: bool) -> None:
        node_type = node.get('WebBookmarkType', '')
        title     = node.get('Title') or node.get('URIDictionary', {}).get('title', '')

        if node_type == 'WebBookmarkTypeList':
            if title in SKIP_FOLDERS:
                return
            # If a folder filter is set, activate collection once we enter a matching folder
            now_inside = inside_match or (
                folder_filter is not None and folder_filter.lower() in title.lower()
            )
            # When no filter is set, collect from everywhere
            collect = folder_filter is None or now_inside
            for child in node.get('Children', []):
                _walk_with_collect(child, collect, now_inside)

        elif node_type == 'WebBookmarkTypeLeaf':
            if inside_match or folder_filter is None:
                url = node.get('URLString', '')
                if url.startswith(('http://', 'https://')):
                    results.append({'title': _UNREAD_COUNT_RE.sub('', title or url), 'url': url})

    def _walk_with_collect(node: dict, collect: bool, inside_match: bool) -> None:
        node_type = node.get('WebBookmarkType', '')
        title     = node.get('Title') or node.get('URIDictionary', {}).get('title', '')

        if node_type == 'WebBookmarkTypeList':
            if title in SKIP_FOLDERS:
                return
            now_inside = inside_match or (
                folder_filter is not None and folder_filter.lower() in title.lower()
            )
            now_collect = collect or (folder_filter is not None and now_inside)
            for child in node.get('Children', []):
                _walk_with_collect(child, now_collect, now_inside)

        elif node_type == 'WebBookmarkTypeLeaf':
            if collect:
                url = node.get('URLString', '')
                if url.startswith(('http://', 'https://')):
                    results.append({'title': _UNREAD_COUNT_RE.sub('', title or url), 'url': url})

    for child in data.get('Children', []):
        top_title = child.get('Title') or child.get('URIDictionary', {}).get('title', '')
        if top_title in SKIP_FOLDERS or child.get('WebBookmarkIdentifier') in SKIP_FOLDERS:
            continue
        _walk_with_collect(child, folder_filter is None, False)

    return results


def list_bookmark_folders() -> None:
    if not os.path.exists(BOOKMARKS_PLIST):
        sys.exit(f'ERROR: {BOOKMARKS_PLIST} not found.')

    with open(BOOKMARKS_PLIST, 'rb') as f:
        data = plistlib.load(f)

    def walk(node: dict, depth: int) -> None:
        node_type = node.get('WebBookmarkType', '')
        title     = node.get('Title') or node.get('URIDictionary', {}).get('title', '')
        if node_type == 'WebBookmarkTypeList':
            if title in SKIP_FOLDERS:
                return
            kids      = node.get('Children', [])
            leaf_count = sum(
                1 for k in kids
                if k.get('WebBookmarkType') == 'WebBookmarkTypeLeaf'
                and k.get('URLString', '').startswith(('http://', 'https://'))
            )
            sub_count  = sum(1 for k in kids if k.get('WebBookmarkType') == 'WebBookmarkTypeList')
            print(f'{"  " * depth}{title!r}  ({leaf_count} bookmarks, {sub_count} subfolders)')
            for child in kids:
                walk(child, depth + 1)

    for child in data.get('Children', []):
        walk(child, 0)


# ---------------------------------------------------------------------------
# Post to JTTBH
# ---------------------------------------------------------------------------

def post_import(items: list[dict]) -> dict:
    if not JTTBH_API_KEY:
        sys.exit(
            'ERROR: JTTBH_IMPORT_KEY env var is not set.\n'
            'Set it to the value of IMPORT_API_KEY in your production .env.'
        )

    url     = f'{JTTBH_URL}/{JTTBH_USERNAME}/bookmark/import/post'
    payload = json.dumps(items).encode()
    req     = urllib.request.Request(
        url,
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'X-Api-Key':    JTTBH_API_KEY,
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        sys.exit(f'ERROR: HTTP {e.code} from server.\n{body}')
    except urllib.error.URLError as e:
        sys.exit(f'ERROR: Could not reach {url}.\n{e.reason}')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Import Safari tabs or bookmarks into JTTBH.')
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list',      action='store_true', help='List available iCloud tab devices and exit')
    group.add_argument('--device',    metavar='NAME',      help='Import tabs from device (partial name, case-insensitive)')
    group.add_argument('--all',       action='store_true', help='Import tabs from all devices')
    group.add_argument('--bookmarks', action='store_true', help='Import Safari bookmarks (Favorites + Bookmarks Menu)')
    group.add_argument('--folders',   action='store_true', help='List bookmark folders and exit')
    parser.add_argument('--folder',   metavar='NAME',      help='With --bookmarks: only import from this folder (partial match)')
    parser.add_argument('--dry-run',  action='store_true', help='Print what would be imported without posting')
    args = parser.parse_args()

    # --- bookmark folder listing ---
    if args.folders:
        list_bookmark_folders()
        return

    # --- bookmark import ---
    if args.bookmarks:
        items = get_bookmarks(args.folder)
        label = f'folder {args.folder!r}' if args.folder else 'all bookmark folders'

        if not items:
            print(f'No bookmarks found in {label}.')
            return

        print(f'Found {len(items)} bookmark(s) from {label}:')
        for b in items:
            print(f'  {b["title"][:60]!r}')
            print(f'    {b["url"]}')

        if args.dry_run:
            print('\n[dry run] Nothing posted.')
            return

        print(f'\nPosting to {JTTBH_URL}/{JTTBH_USERNAME}/bookmark/import/post …')
        result = post_import(items)
        print(f"  Imported : {result.get('imported', '?')}")
        print(f"  Skipped  : {result.get('skipped',  '?')}  (already bookmarked)")
        print(f"  Errors   : {result.get('errors',   '?')}  (invalid URLs)")
        return

    # --- tab import ---
    conn    = open_db()
    devices = get_devices(conn)

    if args.list:
        print(f'Devices in CloudTabs.db ({len(devices)}):')
        for d in devices:
            count = conn.execute(
                'SELECT COUNT(*) FROM cloud_tabs WHERE device_uuid = ?', (d['uuid'],)
            ).fetchone()[0]
            print(f'  {d["name"]!r:40s}  {count} tab(s)')
        conn.close()
        return

    if args.all:
        target_uuids = None
        label = 'all devices'
    else:
        matches = [d for d in devices if args.device.lower() in d['name'].lower()]
        if not matches:
            names = [d['name'] for d in devices]
            sys.exit(f'ERROR: No device matching {args.device!r}.\nAvailable: {names}')
        target_uuids = [d['uuid'] for d in matches]
        label = ', '.join(d['name'] for d in matches)

    tabs = get_tabs(conn, target_uuids)
    conn.close()

    if not tabs:
        print(f'No open tabs found for {label}.')
        return

    print(f'Found {len(tabs)} tab(s) from {label}:')
    for t in tabs:
        print(f'  {t["title"][:60]!r}')
        print(f'    {t["url"]}')

    if args.dry_run:
        print('\n[dry run] Nothing posted.')
        return

    print(f'\nPosting to {JTTBH_URL}/{JTTBH_USERNAME}/bookmark/import/post …')
    result = post_import(tabs)
    print(f"  Imported : {result.get('imported', '?')}")
    print(f"  Skipped  : {result.get('skipped',  '?')}  (already bookmarked)")
    print(f"  Errors   : {result.get('errors',   '?')}  (invalid URLs)")


if __name__ == '__main__':
    main()
