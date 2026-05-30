"""
Steam Web API wrapper — minimal surface for the media tracker.

Credentials are stored per-user in user_preference:
  steam_api_key  — from https://steamcommunity.com/dev/apikey
  steam_id       — 64-bit SteamID (e.g. 76561198012345678)
"""

import json
import urllib.error
import urllib.parse
import urllib.request

BASE     = "https://api.steampowered.com"
COVER    = "https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg"


def _get(path: str, params: dict) -> dict | None:
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except Exception:
        return None


def get_owned_games(api_key: str, steam_id: str) -> list[dict]:
    """
    Return the user's full Steam library.

    Each dict has:
      appid            int
      name             str
      playtime_forever int  (minutes; 0 = never played)
      cover_url        str
    """
    data = _get(
        "/IPlayerService/GetOwnedGames/v0001/",
        {
            "key":                  api_key,
            "steamid":              steam_id,
            "include_appinfo":      1,
            "include_played_free_games": 1,
            "format":               "json",
        },
    )
    if not data:
        return []
    games = data.get("response", {}).get("games", [])
    return [
        {
            "appid":            g["appid"],
            "name":             g.get("name", f"App {g['appid']}"),
            "playtime_forever": g.get("playtime_forever", 0),
            "cover_url":        COVER.format(appid=g["appid"]),
        }
        for g in games
    ]
