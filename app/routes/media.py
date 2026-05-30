"""
Media Tracker Routes
====================

GET  /<username>/media/index
GET  /<username>/media/detail/<media_id>
GET  /<username>/media/search/json?q=<query>&kind=<show|movie|any>

POST /<username>/media/create/post
POST /<username>/media/update/post/<media_id>
POST /<username>/media/delete/post/<media_id>
POST /<username>/media/sync/post/<media_id>
POST /<username>/media/episode/seen/post/<episode_id>
"""

import xml.etree.ElementTree as ET
import urllib.request
from collections import defaultdict
from datetime import datetime, date

from flask import (
    Blueprint, flash, jsonify, redirect, render_template,
    request, session, url_for,
)

from app.services.database import db_manager
from app.services.decorators import (
    PERM_BOOK, login_required,
    permission_required_read, permission_required_write,
)
from app.models.media_model import (
    get_all, get_one, create, update, soft_delete,
    get_episodes, upsert_episode, set_seen,
)
import app.services.tmdb as tmdb

media_bp = Blueprint('media', __name__)

VALID_KINDS    = ('book', 'movie', 'show', 'podcast')
VALID_STATUSES = ('want', 'in_progress', 'done', 'dismiss')

KIND_LABELS = {
    'show':    'Shows',
    'movie':   'Movies',
    'podcast': 'Podcasts',
    'book':    'Books',
}
KIND_ORDER   = ['show', 'movie', 'podcast', 'book']
STATUS_ORDER = ['in_progress', 'want', 'done', 'dismiss']
STATUS_LABELS = {
    'in_progress': 'In Progress',
    'want':        'Want to Watch / Read',
    'done':        'Done',
    'dismiss':     'Dismissed',
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _redirect_index(username):
    return redirect(url_for('media.index', username=username))


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None


def _sync_show(media_item: dict, user_id: str):
    """Fetch TMDB details + all episodes and store them."""
    tmdb_id = media_item.get('external_id')
    if not tmdb_id:
        return
    details = tmdb.show_details(tmdb_id)
    if not details:
        return
    update(user_id, media_item,
           streaming=details['streaming'],
           next_date=details['next_date'],
           cover_url=details['cover_url'] or media_item.get('cover_url'))
    for s in range(1, details['seasons'] + 1):
        for ep in tmdb.show_season(tmdb_id, s):
            upsert_episode(
                media_id=media_item['mediaID'],
                external_id=ep['external_id'],
                title=ep['title'],
                season=s,
                episode_number=ep['episode_number'],
                air_date=ep['air_date'],
                description=ep['description'],
                user_id=user_id,
            )


def _sync_movie(media_item: dict, user_id: str):
    tmdb_id = media_item.get('external_id')
    if not tmdb_id:
        return
    details = tmdb.movie_details(tmdb_id)
    if not details:
        return
    update(user_id, media_item,
           cover_url=details['cover_url'] or media_item.get('cover_url'),
           next_date=details['next_date'])


_ITUNES = 'http://www.itunes.com/dtds/podcast-1.0.dtd'

def _sync_podcast(media_item: dict, user_id: str):
    """Fetch RSS feed and store episodes."""
    feed_url = media_item.get('external_id')
    if not feed_url or not feed_url.startswith('http'):
        return
    try:
        with urllib.request.urlopen(feed_url, timeout=10) as r:
            xml_bytes = r.read()
    except Exception:
        return
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return
    channel = root.find('channel')
    if channel is None:
        return
    for i, item in enumerate(channel.findall('item')):
        title_el = item.find('title')
        title = title_el.text.strip() if title_el is not None and title_el.text else f'Episode {i+1}'
        guid_el = item.find('guid')
        enc_el  = item.find('enclosure')
        guid = (guid_el.text or '').strip() if guid_el is not None else ''
        if not guid and enc_el is not None:
            guid = enc_el.get('url', '')
        if not guid:
            continue
        pub_el = item.find('pubDate')
        air_date = None
        if pub_el is not None and pub_el.text:
            for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S %Z'):
                try:
                    air_date = datetime.strptime(pub_el.text.strip(), fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    pass
        desc_el = item.find(f'{{{_ITUNES}}}summary') or item.find('description')
        description = desc_el.text.strip() if desc_el is not None and desc_el.text else None
        upsert_episode(
            media_id=media_item['mediaID'],
            external_id=guid,
            title=title,
            season=None,
            episode_number=i + 1,
            air_date=air_date,
            description=description,
            user_id=user_id,
        )


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@media_bp.route('/index')
@login_required
@permission_required_read(PERM_BOOK)
def index(username: str):
    user_id = session['user_id']
    all_items = get_all(user_id)

    # Group by kind, then by status
    grouped: dict[str, dict[str, list]] = {
        kind: {s: [] for s in STATUS_ORDER} for kind in KIND_ORDER
    }
    for item in all_items:
        kind   = item.get('kind', 'book')
        status = item.get('status', 'want')
        if kind in grouped and status in grouped[kind]:
            grouped[kind][status].append(item)

    return render_template('media_index.html',
                           username=username,
                           area='book',
                           grouped=grouped,
                           kind_order=KIND_ORDER,
                           kind_labels=KIND_LABELS,
                           status_order=STATUS_ORDER,
                           status_labels=STATUS_LABELS)


@media_bp.route('/detail/<media_id>')
@login_required
@permission_required_read(PERM_BOOK)
def detail(username: str, media_id: str):
    user_id = session['user_id']
    item = get_one(user_id, media_id)
    if item is None:
        flash('Media item not found.', 'error')
        return _redirect_index(username)

    episodes = get_episodes(media_id) if item['kind'] in ('show', 'podcast') else []

    # Group show episodes by season
    by_season: dict = defaultdict(list)
    for ep in episodes:
        by_season[ep['season']].append(ep)

    return render_template('media_detail.html',
                           username=username,
                           area='book',
                           item=item,
                           episodes=episodes,
                           by_season=dict(sorted(by_season.items(), key=lambda x: (x[0] is None, x[0]))),
                           status_labels=STATUS_LABELS)


@media_bp.route('/search/json')
@login_required
@permission_required_read(PERM_BOOK)
def search_json(username: str):
    q    = request.args.get('q', '').strip()
    kind = request.args.get('kind', 'any')
    if not q:
        return jsonify([])
    results = tmdb.search(q, kind)
    return jsonify(results)


# ---------------------------------------------------------------------------
# POST routes (PRG pattern)
# ---------------------------------------------------------------------------

@media_bp.route('/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOK)
@permission_required_write(PERM_BOOK)
def create_item(username: str):
    user_id = session['user_id']
    title   = request.form.get('title', '').strip()
    kind    = request.form.get('kind', 'book')
    if not title:
        flash('Title is required.', 'error')
        return _redirect_index(username)
    if kind not in VALID_KINDS:
        kind = 'book'

    creator     = request.form.get('creator', '').strip() or None
    status      = request.form.get('status', 'want')
    external_id = request.form.get('external_id', '').strip() or None
    cover_url   = request.form.get('cover_url', '').strip() or None

    if status not in VALID_STATUSES:
        status = 'want'

    started  = user_today_date() if status == 'in_progress' else None
    finished = user_today_date() if status == 'done' else None

    media_id = create(user_id, title, kind, creator, status,
                      external_id=external_id, cover_url=cover_url,
                      started=started, finished=finished)

    # Auto-sync external data on create
    item = get_one(user_id, media_id)
    if item and kind == 'show' and external_id:
        try:
            _sync_show(item, user_id)
        except Exception:
            pass
    elif item and kind == 'movie' and external_id:
        try:
            _sync_movie(item, user_id)
        except Exception:
            pass
    elif item and kind == 'podcast' and external_id:
        try:
            _sync_podcast(item, user_id)
        except Exception:
            pass

    flash(f'"{title}" added.', 'success')
    if kind in ('show', 'podcast'):
        return redirect(url_for('media.detail', username=username, media_id=media_id))
    return _redirect_index(username)


@media_bp.route('/update/post/<media_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOK)
@permission_required_write(PERM_BOOK)
def update_item(username: str, media_id: str):
    user_id = session['user_id']
    item = get_one(user_id, media_id)
    if item is None:
        flash('Media item not found.', 'error')
        return _redirect_index(username)

    status = request.form.get('status', item['status'])
    if status not in VALID_STATUSES:
        status = item['status']

    rating_s = request.form.get('rating', '').strip()
    rating = int(rating_s) if rating_s.isdigit() and 1 <= int(rating_s) <= 5 else item.get('rating')

    review   = request.form.get('review',  '').strip() or item.get('review')
    creator  = request.form.get('creator', '').strip() or item.get('creator')
    started  = _parse_date(request.form.get('started'))  or item.get('started')
    finished = _parse_date(request.form.get('finished')) or item.get('finished')

    if status == 'in_progress' and not started:
        started = user_today_date()
    if status == 'done' and not finished:
        finished = user_today_date()

    update(user_id, item,
           status=status, rating=rating, review=review or None,
           creator=creator or None, started=started, finished=finished)

    flash('Updated.', 'success')
    if item['kind'] in ('show', 'podcast'):
        return redirect(url_for('media.detail', username=username, media_id=media_id))
    return _redirect_index(username)


@media_bp.route('/delete/post/<media_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOK)
@permission_required_write(PERM_BOOK)
def delete_item(username: str, media_id: str):
    user_id = session['user_id']
    item = get_one(user_id, media_id)
    if item is None:
        flash('Media item not found.', 'error')
        return _redirect_index(username)
    soft_delete(user_id, media_id)
    flash(f'"{item["title"]}" removed.', 'success')
    return _redirect_index(username)


@media_bp.route('/sync/post/<media_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOK)
@permission_required_write(PERM_BOOK)
def sync_item(username: str, media_id: str):
    user_id = session['user_id']
    item = get_one(user_id, media_id)
    if item is None:
        flash('Media item not found.', 'error')
        return _redirect_index(username)
    kind = item['kind']
    try:
        if kind == 'show':
            _sync_show(item, user_id)
        elif kind == 'movie':
            _sync_movie(item, user_id)
        elif kind == 'podcast':
            _sync_podcast(item, user_id)
        flash('Synced.', 'success')
    except Exception as e:
        flash(f'Sync failed: {e}', 'error')
    if kind in ('show', 'podcast'):
        return redirect(url_for('media.detail', username=username, media_id=media_id))
    return _redirect_index(username)


@media_bp.route('/episode/seen/post/<episode_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOK)
@permission_required_write(PERM_BOOK)
def episode_seen(username: str, episode_id: str):
    seen = request.form.get('seen', '0') == '1'
    set_seen(episode_id, seen)
    media_id = request.form.get('media_id', '')
    if media_id:
        return redirect(url_for('media.detail', username=username, media_id=media_id))
    return _redirect_index(username)


# ---------------------------------------------------------------------------
# Compat redirect from old /book/index
# ---------------------------------------------------------------------------

def user_today_date():
    try:
        from app.services.timezone_utils import user_today
        return user_today()
    except Exception:
        return date.today()
