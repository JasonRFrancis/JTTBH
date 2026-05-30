"""
TMDB API wrapper — minimal surface for the media tracker.

Reads TMDB_API_KEY from app config via Flask's current_app.
All functions return plain dicts/lists; callers handle None on error.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

from flask import current_app

BASE = "https://api.themoviedb.org/3"
IMG  = "https://image.tmdb.org/t/p/w300"


def _get(path: str, params: dict) -> dict | None:
    key = current_app.config.get('TMDB_API_KEY', '')
    if not key:
        return None
    params['api_key'] = key
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            return json.loads(r.read())
    except Exception:
        return None


def search(query: str, kind: str) -> list[dict]:
    """Search TMDB. kind: 'show' | 'movie' | 'any'."""
    endpoint = '/search/tv' if kind == 'show' else '/search/movie' if kind == 'movie' else '/search/multi'
    data = _get(endpoint, {'query': query, 'language': 'en-US', 'page': 1})
    if not data:
        return []
    results = []
    for r in data.get('results', [])[:8]:
        media_type = r.get('media_type', kind if kind != 'any' else '')
        if kind == 'any' and media_type not in ('tv', 'movie'):
            continue
        title = r.get('name') or r.get('title') or ''
        year = (r.get('first_air_date') or r.get('release_date') or '')[:4]
        poster = (IMG + r['poster_path']) if r.get('poster_path') else ''
        results.append({
            'id':         str(r['id']),
            'title':      title,
            'year':       year,
            'kind':       'show' if r.get('media_type') == 'tv' or kind == 'show' else 'movie',
            'cover_url':  poster,
        })
    return results


def show_details(tmdb_id: str) -> dict | None:
    """Return streaming service string and next air date for a TV show."""
    data = _get(f'/tv/{tmdb_id}', {'language': 'en-US', 'append_to_response': 'watch/providers'})
    if not data:
        return None

    # Streaming providers (US flat/subscription tier)
    streaming = ''
    providers = data.get('watch/providers', {}).get('results', {}).get('US', {})
    flatrate = providers.get('flatrate', [])
    if flatrate:
        streaming = ', '.join(p['provider_name'] for p in flatrate[:4])

    next_ep = data.get('next_episode_to_air')
    next_date = next_ep['air_date'] if next_ep else None

    poster = (IMG + data['poster_path']) if data.get('poster_path') else ''

    return {
        'streaming': streaming,
        'next_date': next_date,
        'cover_url': poster,
        'seasons':   data.get('number_of_seasons', 0),
    }


def show_season(tmdb_id: str, season: int) -> list[dict]:
    """Return episode list for one TV season."""
    data = _get(f'/tv/{tmdb_id}/season/{season}', {'language': 'en-US'})
    if not data:
        return []
    episodes = []
    for ep in data.get('episodes', []):
        episodes.append({
            'external_id':    str(ep['id']),
            'episode_number': ep.get('episode_number'),
            'title':          ep.get('name', ''),
            'air_date':       ep.get('air_date') or None,
            'description':    ep.get('overview', '') or None,
        })
    return episodes


def movie_details(tmdb_id: str) -> dict | None:
    """Return cover and release date for a movie."""
    data = _get(f'/movie/{tmdb_id}', {'language': 'en-US'})
    if not data:
        return None
    poster = (IMG + data['poster_path']) if data.get('poster_path') else ''
    return {
        'cover_url':  poster,
        'next_date':  data.get('release_date') or None,
    }
