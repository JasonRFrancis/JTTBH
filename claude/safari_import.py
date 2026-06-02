"""
safari_import.py — import open Safari tabs from iCloud-connected devices
into the JTTBH bookmarks page (marked as Read Later).

Prerequisites
-------------
1. Full Disk Access granted to your terminal app:
   System Settings → Privacy & Security → Full Disk Access → add Terminal / iTerm2

2. IMPORT_API_KEY set in production .env (same value used here):
   Generate one with:  python3 -c "import secrets; print(secrets.token_hex(32))"

3. Env var (or hard-code below):
   export JTTBH_IMPORT_KEY=<your_key>

Usage
-----
  # List available devices
  python3 claude/safari_import.py --list

  # Import tabs from a specific device (partial name match, case-insensitive)
  python3 claude/safari_import.py --device "iphone"

  # Import from all devices
  python3 claude/safari_import.py --all

  # Dry run (prints what would be imported without posting)
  python3 claude/safari_import.py --device "iphone" --dry-run
"""

import argparse
import json
import os
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

CLOUD_TABS_DB  = os.path.expanduser('~/Library/Safari/CloudTabs.db')

# ---------------------------------------------------------------------------
# Read CloudTabs.db
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

    # Fallback: derive device list from tabs table
    if 'cloud_tabs' in tables:
        rows = conn.execute("SELECT DISTINCT device_uuid FROM cloud_tabs").fetchall()
        return [{'uuid': r['device_uuid'], 'name': r['device_uuid'][:8]} for r in rows]

    sys.exit('ERROR: Could not find device table in CloudTabs.db. Schema may have changed.')


def get_tabs(conn: sqlite3.Connection, device_uuids: list[str] | None) -> list[dict]:
    """
    Return list of {title, url} dicts.
    If device_uuids is None, return tabs from all devices.
    """
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if 'cloud_tabs' not in tables:
        sys.exit('ERROR: cloud_tabs table not found in CloudTabs.db.')

    cols = {r[1] for r in conn.execute('PRAGMA table_info(cloud_tabs)').fetchall()}
    order_col = 'position_index' if 'position_index' in cols else 'rowid'

    if device_uuids:
        placeholders = ','.join('?' * len(device_uuids))
        rows = conn.execute(
            f'SELECT title, url, device_uuid FROM cloud_tabs WHERE device_uuid IN ({placeholders}) ORDER BY {order_col}',
            device_uuids,
        ).fetchall()
    else:
        rows = conn.execute(
            f'SELECT title, url, device_uuid FROM cloud_tabs ORDER BY {order_col}'
        ).fetchall()

    return [{'title': r['title'] or r['url'], 'url': r['url']} for r in rows if r['url']]


# ---------------------------------------------------------------------------
# Post to JTTBH
# ---------------------------------------------------------------------------

def post_import(tabs: list[dict]) -> dict:
    if not JTTBH_API_KEY:
        sys.exit(
            'ERROR: JTTBH_IMPORT_KEY env var is not set.\n'
            'Set it to the value of IMPORT_API_KEY in your production .env.'
        )

    url     = f'{JTTBH_URL}/{JTTBH_USERNAME}/bookmark/import/post'
    payload = json.dumps(tabs).encode()
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
    parser = argparse.ArgumentParser(description='Import Safari iCloud tabs into JTTBH bookmarks.')
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list',   action='store_true', help='List available devices and exit')
    group.add_argument('--device', metavar='NAME',       help='Device name to import from (partial, case-insensitive)')
    group.add_argument('--all',    action='store_true',  help='Import tabs from all devices')
    parser.add_argument('--dry-run', action='store_true', help='Print what would be imported without posting')
    args = parser.parse_args()

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
