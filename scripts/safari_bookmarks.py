#!/usr/bin/env python3
"""
safari_bookmarks.py
-------------------
Saves all open Safari tabs as bookmarks on jttbh.com.

Setup:
  1. Go to https://jttbh.com/jason/bookmark/settings and generate an API token.
  2. Paste it into the TOKEN variable below.
  3. Run:  python3 safari_bookmarks.py
  4. Optional flags:
       --read-later   mark every tab as Read Later
       --tags foo,bar attach tags to every bookmark
       --dry-run      print URLs without saving
"""

import argparse
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import json

# ── Configuration ─────────────────────────────────────────────────────────────

TOKEN    = "38ddb856a73551826c304146022e4ccedcfcca529d7c09d12231b51645e396cc"
USERNAME = "jason"
API_URL  = f"https://jttbh.com/{USERNAME}/bookmark/api/create"

# ─────────────────────────────────────────────────────────────────────────────


def get_safari_tabs() -> list[tuple[str, str]]:
    """Return list of (url, title) for every open Safari tab."""
    script = """
tell application "Safari"
    set output to ""
    repeat with w in windows
        if visible of w then
            repeat with t in tabs of w
                set output to output & (URL of t) & "\t" & (name of t) & "\n"
            end repeat
        end if
    end repeat
    output
end tell
"""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"AppleScript error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    tabs = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2:
            url, title = parts[0].strip(), parts[1].strip()
        else:
            url, title = parts[0].strip(), ""
        if url.startswith("http"):
            tabs.append((url, title))
    return tabs


def save_bookmark(url: str, title: str, tags: str, read_later: bool) -> dict:
    data = urllib.parse.urlencode({
        "token":      TOKEN,
        "url":        url,
        "title":      title,
        "tags":       tags,
        "read_later": "1" if read_later else "0",
    }).encode()
    req = urllib.request.Request(API_URL, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser(description="Save Safari tabs to jttbh bookmarks")
    parser.add_argument("--read-later", action="store_true", help="Mark all tabs as Read Later")
    parser.add_argument("--tags", default="", help="Comma-separated tags to apply to all bookmarks")
    parser.add_argument("--dry-run", action="store_true", help="Print tabs without saving")
    args = parser.parse_args()

    if TOKEN == "PASTE_YOUR_TOKEN_HERE":
        print("Error: paste your API token into the TOKEN variable at the top of this script.")
        sys.exit(1)

    tabs = get_safari_tabs()
    if not tabs:
        print("No Safari tabs found.")
        return

    print(f"Found {len(tabs)} tab(s).")

    saved = failed = 0
    for url, title in tabs:
        if args.dry_run:
            print(f"  [dry-run] {url}")
            continue
        try:
            result = save_bookmark(url, title, args.tags, args.read_later)
            if result.get("status") == "ok":
                print(f"  ✓  {title or url}")
                saved += 1
            else:
                print(f"  ✗  {url}  ({result.get('message', 'unknown error')})")
                failed += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"  ✗  {url}  (HTTP {e.code}: {body})")
            failed += 1
        except Exception as e:
            print(f"  ✗  {url}  ({e})")
            failed += 1

    if not args.dry_run:
        print(f"\nDone. {saved} saved" + (f", {failed} failed." if failed else "."))


if __name__ == "__main__":
    main()
