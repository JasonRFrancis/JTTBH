#!/usr/bin/env python3
"""
watch_later.py
--------------
Import YouTube Watch Later into jttbh.com bookmarks, then delete them.

Commands
--------
  python3 watch_later.py import   Extract Watch Later via yt-dlp → save to
                                  watch_later.json → import to jttbh bookmarks.
  python3 watch_later.py delete   Remove every video in watch_later.json from
                                  your YouTube Watch Later playlist.
  python3 watch_later.py auth     (Only needed for `delete`) Open browser for
                                  YouTube login and save the session.

Setup
-----
  1. pip install yt-dlp playwright && python3 -m playwright install chromium
  2. Set TOKEN below (from jttbh.com/<username>/bookmark/settings).
  3. Run `import` — yt-dlp reads your Chrome cookies automatically.
  4. Confirm bookmarks on jttbh.com, then run `auth` + `delete`.
"""

import json
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ── Configuration ─────────────────────────────────────────────────────────────

TOKEN    = "38ddb856a73551826c304146022e4ccedcfcca529d7c09d12231b51645e396cc"
USERNAME = "jason"
API_URL  = f"https://jttbh.com/{USERNAME}/bookmark/api/create"
TAGS     = "watchlater"

WL_URL = "https://www.youtube.com/playlist?list=WL"

HERE        = Path(__file__).parent
STATE_FILE  = HERE / "yt_auth.json"
VIDEOS_FILE = HERE / "watch_later.json"

# ─────────────────────────────────────────────────────────────────────────────


def _browser_context(p):
    kwargs = dict(viewport={"width": 1280, "height": 800}, locale="en-US")
    if STATE_FILE.exists():
        kwargs["storage_state"] = str(STATE_FILE)
    return p.chromium.launch(headless=False, channel="chrome").new_context(**kwargs)


# ── Auth (only needed for `delete`) ──────────────────────────────────────────

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CDP_PORT   = 9222


def cmd_auth():
    """
    Launch a real Chrome process with remote debugging, let you log into
    YouTube, then save the session cookies for `delete` to use.
    Quit Chrome before running this.
    """
    with tempfile.TemporaryDirectory() as tmp_profile:
        print("Launching Chrome (quit Chrome first if it's open)...")
        proc = subprocess.Popen([
            CHROME_BIN,
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={tmp_profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "https://www.youtube.com",
        ])
        time.sleep(3)

        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
            except Exception as e:
                proc.terminate()
                print(f"Could not connect to Chrome: {e}")
                print("Make sure Chrome is fully quit before running auth.")
                sys.exit(1)

            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            print("Log into YouTube in the Chrome window, then press Enter here...")
            input()
            ctx.storage_state(path=str(STATE_FILE))
            print(f"Session saved to {STATE_FILE}")

        proc.terminate()
        proc.wait()


# ── Scrape via yt-dlp ─────────────────────────────────────────────────────────

def _scrape_with_ytdlp() -> list[dict]:
    """
    Extract the Watch Later playlist using yt-dlp, which reads Chrome's
    cookies directly and handles YouTube's pagination automatically.
    """
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--flat-playlist",
                "--print", "%(id)s\t%(title)s",
                "--cookies-from-browser", "chrome",
                "--quiet",
                WL_URL,
            ],
            capture_output=True, text=True, timeout=600,
        )
    except FileNotFoundError:
        print("yt-dlp not found. Install it:  pip install yt-dlp")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("yt-dlp timed out after 10 minutes.")
        sys.exit(1)

    if result.returncode != 0:
        print(f"yt-dlp error:\n{result.stderr[:800]}")
        sys.exit(1)

    videos = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        vid_id, title = parts[0].strip(), parts[1].strip()
        if vid_id:
            videos.append({
                "title": title,
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "video_id": vid_id,
            })
    return videos


# ── Import ────────────────────────────────────────────────────────────────────

def _save_bookmark(video: dict) -> bool:
    data = urllib.parse.urlencode({
        "token": TOKEN,
        "url":   video["url"],
        "title": video["title"],
        "tags":  TAGS,
    }).encode()
    req = urllib.request.Request(API_URL, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()).get("status") == "ok"
    except urllib.error.HTTPError as e:
        print(f"    HTTP {e.code}: {e.read().decode()[:120]}")
        return False
    except Exception as e:
        print(f"    {e}")
        return False


def cmd_import():
    if TOKEN == "PASTE_YOUR_TOKEN_HERE":
        print("Set TOKEN in the script first.")
        sys.exit(1)

    print("Extracting Watch Later via yt-dlp (this may take a few minutes)...")
    videos = _scrape_with_ytdlp()

    if not videos:
        print("No videos found.")
        return

    print(f"Found {len(videos)} video(s). Saving to {VIDEOS_FILE}...")
    VIDEOS_FILE.write_text(json.dumps(videos, indent=2, ensure_ascii=False))

    print("Importing to jttbh.com...")
    saved = failed = 0
    for v in videos:
        ok = _save_bookmark(v)
        if ok:
            print(f"  ✓  {v['title']}")
            saved += 1
        else:
            print(f"  ✗  {v['title']}  ({v['url']})")
            failed += 1

    print(f"\nDone. {saved} imported" + (f", {failed} failed." if failed else "."))
    print(f"\nConfirm bookmarks at https://jttbh.com/{USERNAME}/bookmark/index")
    print(f"Then run:  python3 watch_later.py auth  (if not done)")
    print(f"           python3 watch_later.py delete")


# ── Delete ────────────────────────────────────────────────────────────────────

def _remove_first_video(page) -> bool:
    """Click the three-dot menu on the first video and choose Remove."""
    try:
        page.wait_for_selector("ytd-playlist-video-renderer", timeout=5_000)
    except PlaywrightTimeout:
        return False

    first = page.locator("ytd-playlist-video-renderer").first
    menu_btn = first.locator("ytd-menu-renderer yt-icon-button#button").last
    menu_btn.scroll_into_view_if_needed()
    menu_btn.click()

    try:
        page.locator("tp-yt-paper-item, ytd-menu-service-item-renderer").filter(
            has_text="Remove from Watch Later"
        ).first.click(timeout=4_000)
    except PlaywrightTimeout:
        page.locator("tp-yt-paper-item").filter(has_text="Remove").first.click(timeout=3_000)

    time.sleep(0.8)
    return True


def cmd_delete():
    if not VIDEOS_FILE.exists():
        print(f"{VIDEOS_FILE} not found. Run `import` first.")
        sys.exit(1)

    videos = json.loads(VIDEOS_FILE.read_text())
    print(f"Will delete {len(videos)} video(s) from Watch Later.")
    print("Press Enter to open YouTube (Ctrl+C to cancel)...")
    input()

    with sync_playwright() as p:
        ctx = _browser_context(p)
        page = ctx.new_page()
        page.goto(WL_URL, wait_until="domcontentloaded")

        try:
            page.wait_for_selector("ytd-playlist-video-renderer", timeout=10_000)
        except PlaywrightTimeout:
            print("Watch Later is empty or you're not logged in.")
            ctx.browser.close()
            return

        print("Removing videos (this will take a while for large playlists)...")

        removed = 0
        failures = 0
        while True:
            if removed > 0 and removed % 200 == 0:
                page.reload(wait_until="domcontentloaded")
                try:
                    page.wait_for_selector("ytd-playlist-video-renderer", timeout=10_000)
                except PlaywrightTimeout:
                    break

            ok = _remove_first_video(page)
            if not ok:
                failures += 1
                if failures >= 5:
                    break
                time.sleep(2)
                continue
            failures = 0
            removed += 1
            print(f"  Removed {removed}...", end="\r")

        print(f"\nDone. Removed {removed} video(s).")
        ctx.storage_state(path=str(STATE_FILE))
        ctx.browser.close()


# ── Entry point ───────────────────────────────────────────────────────────────

COMMANDS = {"auth": cmd_auth, "import": cmd_import, "delete": cmd_delete}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print("Usage: python3 watch_later.py <import|delete|auth>")
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
