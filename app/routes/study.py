"""
Study Routes
============
Daily study content drawn from subscribed collections of sources.

URL patterns
------------
GET  /<username>/study/index
GET  /<username>/study/index/<date_str>
GET  /<username>/study/collections
GET  /<username>/study/collection/<collection_id>
GET  /<username>/study/subscription/<subscription_id>/edit
GET  /<username>/study/subscription/<subscription_id>/schedule

POST /<username>/study/collection/create/post
POST /<username>/study/collection/update/post/<collection_id>
POST /<username>/study/collection/delete/post/<collection_id>
POST /<username>/study/source/create/post
POST /<username>/study/source/update/post/<source_id>
POST /<username>/study/source/delete/post/<source_id>
POST /<username>/study/subscribe/post/<collection_id>
POST /<username>/study/subscription/update/post/<subscription_id>
POST /<username>/study/unsubscribe/post/<subscription_id>
POST /<username>/study/source/complete/post/<source_id>
POST /<username>/study/subscription/<subscription_id>/schedule/set/post
POST /<username>/study/subscription/<subscription_id>/schedule/clear/post/<source_id>
"""

import json
from datetime import date, timedelta

from flask import (
    Blueprint,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.models.study_model import StudyModel
from app.services.database import db_manager
from app.services.decorators import (
    login_required,
    permission_required_read,
    permission_required_write,
    PERM_STUDY,
)
from app.services.timezone_utils import user_today, today_for_tz

study_bp = Blueprint('study', __name__)


def _parse_date(date_str: str) -> date | None:
    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


_VALID_PER_DAY = {-7, -2, -1} | set(range(1, 8))  # weekly/odd/even + 1–7 per day

def _parse_per_day(raw: str) -> int:
    try:
        v = int(raw.strip())
    except (ValueError, AttributeError):
        return 1
    return v if v in _VALID_PER_DAY else 1


def _normalise_csv(raw: str) -> str:
    """Deduplicate and strip a comma-separated string; return '' if empty."""
    parts = [p.strip() for p in raw.split(',') if p.strip()]
    seen = []
    for p in parts:
        if p not in seen:
            seen.append(p)
    return ', '.join(seen)


# ---------------------------------------------------------------------------
# Daily index
# ---------------------------------------------------------------------------

@study_bp.route('/index')
@study_bp.route('/index/<date_str>')
@login_required
@permission_required_read(PERM_STUDY)
def index(username: str, date_str: str = None):
    today = today_for_tz(session.get('timezone', 'UTC'))
    target_date = _parse_date(date_str) if date_str else today
    if target_date is None:
        return redirect(url_for('study.index', username=username))

    user_id = session['user_id']
    subscriptions = StudyModel.get_user_subscriptions(user_id)

    day_sources = []
    for sub in subscriptions:
        sources = StudyModel.get_sources(sub['collectionID'])
        items = StudyModel.sources_for_date(sub, sources, target_date, user_id)
        if items:
            day_sources.append({
                'display_name': sub.get('subscription_name') or sub['collection_name'],
                'collection_name': sub['collection_name'],
                'collection_id': sub['collectionID'],
                'subscription_id': sub['subscriptionID'],
                'mode': sub['mode'],
                'use_personal_schedule': sub.get('use_personal_schedule', 0),
                'sources': items,
            })

    completions = StudyModel.get_completions_for_date(user_id, target_date)
    streak = StudyModel.calculate_streak(user_id, today)

    return render_template(
        'study_index.html',
        username=username,
        area='study',
        target_date=target_date,
        today=today,
        prev_date=target_date - timedelta(days=1),
        next_date=target_date + timedelta(days=1),
        day_sources=day_sources,
        has_subscriptions=bool(subscriptions),
        completions=completions,
        streak=streak,
    )


# ---------------------------------------------------------------------------
# Collections browser
# ---------------------------------------------------------------------------

@study_bp.route('/collections')
@login_required
@permission_required_read(PERM_STUDY)
def collections(username: str):
    all_collections = StudyModel.get_all_collections()
    subs_list = StudyModel.get_user_subscriptions(session['user_id'])
    user_subs: dict[str, list] = {}
    for s in subs_list:
        user_subs.setdefault(s['collectionID'], []).append(s)
    today = today_for_tz(session.get('timezone', 'UTC'))
    return render_template(
        'study_collections.html',
        username=username,
        area='study',
        collections=all_collections,
        user_subs=user_subs,
        today=today,
    )


# ---------------------------------------------------------------------------
# Collection detail (owner manages sources)
# ---------------------------------------------------------------------------

@study_bp.route('/collection/<collection_id>')
@login_required
@permission_required_read(PERM_STUDY)
def collection_detail(username: str, collection_id: str):
    collection = StudyModel.get_collection(collection_id)
    if not collection:
        flash('Collection not found.', 'error')
        return redirect(url_for('study.collections', username=username))
    if collection['userID'] != session['user_id']:
        flash('Only the collection owner can manage sources.', 'error')
        return redirect(url_for('study.collections', username=username))
    sources = StudyModel.get_sources(collection_id)
    return render_template(
        'study_collection_detail.html',
        username=username,
        area='study',
        collection=collection,
        sources=sources,
    )


# ---------------------------------------------------------------------------
# Subscription edit (smart filters)
# ---------------------------------------------------------------------------

@study_bp.route('/subscription/<subscription_id>/edit')
@login_required
@permission_required_read(PERM_STUDY)
def subscription_edit(username: str, subscription_id: str):
    sub = StudyModel.get_subscription_by_id(subscription_id)
    if not sub or sub['userID'] != session['user_id']:
        flash('Subscription not found.', 'error')
        return redirect(url_for('study.collections', username=username))
    collection = StudyModel.get_collection(sub['collectionID'])
    if not collection:
        flash('Collection not found.', 'error')
        return redirect(url_for('study.collections', username=username))

    distinct_authors    = StudyModel.get_distinct_authors(sub['collectionID'])
    distinct_categories = StudyModel.get_distinct_categories(sub['collectionID'])

    selected_authors = set()
    if sub.get('filter_author'):
        selected_authors = {a.strip() for a in sub['filter_author'].split(',') if a.strip()}
    selected_categories = set()
    if sub.get('filter_category'):
        selected_categories = {c.strip() for c in sub['filter_category'].split(',') if c.strip()}

    all_sources = StudyModel.get_sources(sub['collectionID'])
    today_str   = today_for_tz(session.get('timezone', 'UTC')).isoformat()

    all_sources_json = json.dumps({
        'sources': [
            {
                'sourceID':  s['sourceID'],
                'title':     s['title'] or '',
                'author':    s['author'] or '',
                'category':  s['category'] or '',
                'subtitle':  s['subtitle'] or '',
                'order_by':  s.get('order_by') or 0,
                'has_audio': bool(s.get('audio_url')),
            }
            for s in all_sources
        ],
        'today':       today_str,
        'startOffset': sub.get('start_offset') or 0,
    })

    return render_template(
        'study_subscription_edit.html',
        username=username,
        area='study',
        sub=sub,
        collection=collection,
        distinct_authors=distinct_authors,
        distinct_categories=distinct_categories,
        selected_authors=selected_authors,
        selected_categories=selected_categories,
        total_all=len(all_sources),
        all_sources_json=all_sources_json,
    )


# ---------------------------------------------------------------------------
# Personal schedule view
# ---------------------------------------------------------------------------

@study_bp.route('/subscription/<subscription_id>/schedule')
@login_required
@permission_required_read(PERM_STUDY)
def subscription_schedule(username: str, subscription_id: str):
    sub = StudyModel.get_subscription_by_id(subscription_id)
    if not sub or sub['userID'] != session['user_id']:
        flash('Subscription not found.', 'error')
        return redirect(url_for('study.collections', username=username))
    collection = StudyModel.get_collection(sub['collectionID'])
    if not collection:
        flash('Collection not found.', 'error')
        return redirect(url_for('study.collections', username=username))

    all_sources = StudyModel.get_sources(sub['collectionID'])
    filtered    = StudyModel.get_filtered_sources(sub, all_sources)
    source_ids  = [s['sourceID'] for s in filtered]
    schedule_map = StudyModel.get_personal_schedule_for_sources(session['user_id'], source_ids)

    return render_template(
        'study_schedule.html',
        username=username,
        area='study',
        sub=sub,
        collection=collection,
        sources=filtered,
        schedule_map=schedule_map,
    )


# ---------------------------------------------------------------------------
# Collection CRUD
# ---------------------------------------------------------------------------

@study_bp.route('/collection/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def collection_create(username: str):
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    mode = request.form.get('mode', 'rate')
    if not name:
        flash('Name is required.', 'error')
        return redirect(url_for('study.collections', username=username))
    if mode not in ('rate', 'calendar'):
        mode = 'rate'
    collection_id = StudyModel.create_collection(session['user_id'], name, description, mode)
    flash(f'Collection "{name}" created.', 'success')
    return redirect(url_for('study.collection_detail', username=username, collection_id=collection_id))


@study_bp.route('/collection/update/post/<collection_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def collection_update(username: str, collection_id: str):
    collection = StudyModel.get_collection(collection_id)
    if not collection or collection['userID'] != session['user_id']:
        flash('Collection not found.', 'error')
        return redirect(url_for('study.collections', username=username))
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    mode = request.form.get('mode', 'rate')
    if not name:
        flash('Name is required.', 'error')
        return redirect(url_for('study.collection_detail', username=username, collection_id=collection_id))
    if mode not in ('rate', 'calendar'):
        mode = 'rate'
    StudyModel.update_collection(collection_id, session['user_id'], name, description, mode)
    flash('Collection updated.', 'success')
    return redirect(url_for('study.collection_detail', username=username, collection_id=collection_id))


@study_bp.route('/collection/delete/post/<collection_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def collection_delete(username: str, collection_id: str):
    collection = StudyModel.get_collection(collection_id)
    if not collection or collection['userID'] != session['user_id']:
        flash('Collection not found.', 'error')
        return redirect(url_for('study.collections', username=username))
    StudyModel.delete_collection(collection_id, session['user_id'])
    flash(f'Collection "{collection["name"]}" deleted.', 'success')
    return redirect(url_for('study.collections', username=username))


# ---------------------------------------------------------------------------
# Source CRUD
# ---------------------------------------------------------------------------

@study_bp.route('/source/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def source_create(username: str):
    collection_id = request.form.get('collection_id', '').strip()
    collection = StudyModel.get_collection(collection_id)
    if not collection or collection['userID'] != session['user_id']:
        flash('Collection not found.', 'error')
        return redirect(url_for('study.collections', username=username))
    title = request.form.get('title', '').strip()
    if not title:
        flash('Title is required.', 'error')
        return redirect(url_for('study.collection_detail', username=username, collection_id=collection_id))
    order_by_raw = request.form.get('order_by', '0').strip()
    try:
        order_by = int(order_by_raw)
    except ValueError:
        order_by = 0
    scheduled_date_raw = request.form.get('scheduled_date', '').strip()
    scheduled_date = _parse_date(scheduled_date_raw) if scheduled_date_raw else None

    StudyModel.create_source(
        user_id=session['user_id'],
        collection_id=collection_id,
        category=request.form.get('category', '').strip(),
        title=title,
        subtitle=request.form.get('subtitle', '').strip(),
        author=request.form.get('author', '').strip(),
        url=request.form.get('url', '').strip(),
        audio_url=request.form.get('audio_url', '').strip(),
        audio_length=request.form.get('audio_length', '').strip(),
        order_by=order_by,
        scheduled_date=scheduled_date,
    )
    flash(f'Source "{title}" added.', 'success')
    return redirect(url_for('study.collection_detail', username=username, collection_id=collection_id))


@study_bp.route('/source/update/post/<source_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def source_update(username: str, source_id: str):
    source = StudyModel.get_source(source_id)
    if not source:
        flash('Source not found.', 'error')
        return redirect(url_for('study.collections', username=username))
    collection = StudyModel.get_collection(source['collectionID'])
    if not collection or collection['userID'] != session['user_id']:
        flash('Permission denied.', 'error')
        return redirect(url_for('study.collections', username=username))
    title = request.form.get('title', '').strip()
    if not title:
        flash('Title is required.', 'error')
        return redirect(url_for('study.collection_detail', username=username, collection_id=source['collectionID']))
    order_by_raw = request.form.get('order_by', '0').strip()
    try:
        order_by = int(order_by_raw)
    except ValueError:
        order_by = 0
    scheduled_date_raw = request.form.get('scheduled_date', '').strip()
    scheduled_date = _parse_date(scheduled_date_raw) if scheduled_date_raw else None

    StudyModel.update_source(
        source_id=source_id,
        collection_id=source['collectionID'],
        user_id=session['user_id'],
        category=request.form.get('category', '').strip(),
        title=title,
        subtitle=request.form.get('subtitle', '').strip(),
        author=request.form.get('author', '').strip(),
        url=request.form.get('url', '').strip(),
        audio_url=request.form.get('audio_url', '').strip(),
        audio_length=request.form.get('audio_length', '').strip(),
        order_by=order_by,
        scheduled_date=scheduled_date,
    )
    flash('Source updated.', 'success')
    return redirect(url_for('study.collection_detail', username=username, collection_id=source['collectionID']))


@study_bp.route('/source/delete/post/<source_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def source_delete(username: str, source_id: str):
    source = StudyModel.get_source(source_id)
    if not source:
        flash('Source not found.', 'error')
        return redirect(url_for('study.collections', username=username))
    collection = StudyModel.get_collection(source['collectionID'])
    if not collection or collection['userID'] != session['user_id']:
        flash('Permission denied.', 'error')
        return redirect(url_for('study.collections', username=username))
    StudyModel.delete_source(source_id, source['collectionID'], session['user_id'])
    flash('Source deleted.', 'success')
    return redirect(url_for('study.collection_detail', username=username, collection_id=source['collectionID']))


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------

@study_bp.route('/subscribe/post/<collection_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def subscribe(username: str, collection_id: str):
    collection = StudyModel.get_collection(collection_id)
    if not collection:
        flash('Collection not found.', 'error')
        return redirect(url_for('study.collections', username=username))
    per_day = _parse_per_day(request.form.get('per_day', '1'))
    start_date_raw = request.form.get('start_date', '').strip()
    start_date = _parse_date(start_date_raw) if start_date_raw else today_for_tz(session.get('timezone', 'UTC'))
    name = request.form.get('name', '').strip() or None
    sub_id = StudyModel.create_subscription(session['user_id'], collection_id, per_day, start_date, name)
    flash('Subscribed. Configure filters and name below.', 'success')
    return redirect(url_for('study.subscription_edit', username=username, subscription_id=sub_id))


@study_bp.route('/subscription/update/post/<subscription_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def subscription_update(username: str, subscription_id: str):
    sub = StudyModel.get_subscription_by_id(subscription_id)
    if not sub or sub['userID'] != session['user_id']:
        flash('Subscription not found.', 'error')
        return redirect(url_for('study.collections', username=username))

    per_day = _parse_per_day(request.form.get('per_day', '1'))

    start_date_raw = request.form.get('start_date', '').strip()
    start_date = _parse_date(start_date_raw) if start_date_raw else sub['start_date']

    filter_author   = _normalise_csv(request.form.get('filter_author', ''))
    filter_category = _normalise_csv(request.form.get('filter_category', ''))
    filter_has_audio = 1 if request.form.get('filter_has_audio') else 0
    filter_title = request.form.get('filter_title', '').strip()
    filter_author_text = request.form.get('filter_author_text', '').strip()
    filter_category_text = request.form.get('filter_category_text', '').strip()
    filter_subtitle_text = request.form.get('filter_subtitle_text', '').strip()

    sort_order = request.form.get('sort_order', 'natural')
    if sort_order not in ('natural', 'newest', 'oldest'):
        sort_order = 'natural'

    limit_raw = request.form.get('limit_count', '').strip()
    limit_count = int(limit_raw) if limit_raw.isdigit() and int(limit_raw) > 0 else None

    offset_raw = request.form.get('start_offset', '0').strip()
    try:
        start_offset = max(0, int(offset_raw))
    except ValueError:
        start_offset = 0

    repeat               = 1 if request.form.get('repeat') else 0
    use_personal_schedule = 1 if request.form.get('use_personal_schedule') else 0

    name = request.form.get('name', '').strip() or None
    StudyModel.update_subscription(
        subscription_id, name, per_day, start_date,
        filter_author, filter_category,
        filter_has_audio, filter_title, filter_author_text, filter_category_text,
        filter_subtitle_text,
        sort_order, limit_count, start_offset,
        repeat, use_personal_schedule,
    )
    flash('Subscription updated.', 'success')
    return redirect(url_for('study.subscription_edit', username=username, subscription_id=subscription_id))


@study_bp.route('/unsubscribe/post/<subscription_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def unsubscribe(username: str, subscription_id: str):
    sub = StudyModel.get_subscription_by_id(subscription_id)
    if not sub or sub['userID'] != session['user_id']:
        flash('Subscription not found.', 'error')
        return redirect(url_for('study.collections', username=username))
    StudyModel.delete_subscription(subscription_id)
    flash('Unsubscribed.', 'success')
    return redirect(url_for('study.collections', username=username))


# ---------------------------------------------------------------------------
# Completion toggle
# ---------------------------------------------------------------------------

@study_bp.route('/source/complete/post/<source_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def source_complete(username: str, source_id: str):
    date_str = request.form.get('date', '').strip()
    target_date = _parse_date(date_str) if date_str else today_for_tz(session.get('timezone', 'UTC'))
    now_done = StudyModel.toggle_completion(session['user_id'], source_id, target_date)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'ok', 'done': now_done})
    if date_str:
        return redirect(url_for('study.index', username=username, date_str=date_str))
    return redirect(url_for('study.index', username=username))


# ---------------------------------------------------------------------------
# Personal schedule management
# ---------------------------------------------------------------------------

@study_bp.route('/subscription/<subscription_id>/schedule/set/post', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def schedule_set(username: str, subscription_id: str):
    sub = StudyModel.get_subscription_by_id(subscription_id)
    if not sub or sub['userID'] != session['user_id']:
        flash('Subscription not found.', 'error')
        return redirect(url_for('study.collections', username=username))
    source_id  = request.form.get('source_id', '').strip()
    date_str   = request.form.get('scheduled_date', '').strip()
    target_date = _parse_date(date_str) if date_str else None
    if source_id and target_date:
        StudyModel.set_personal_schedule(session['user_id'], source_id, target_date)
    return redirect(url_for('study.subscription_schedule', username=username, subscription_id=subscription_id))


@study_bp.route('/subscription/<subscription_id>/schedule/clear/post/<source_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def schedule_clear(username: str, subscription_id: str, source_id: str):
    sub = StudyModel.get_subscription_by_id(subscription_id)
    if not sub or sub['userID'] != session['user_id']:
        flash('Subscription not found.', 'error')
        return redirect(url_for('study.collections', username=username))
    StudyModel.clear_personal_schedule(session['user_id'], source_id)
    return redirect(url_for('study.subscription_schedule', username=username, subscription_id=subscription_id))


# ---------------------------------------------------------------------------
# Subscription reorder (JSON endpoint)
# ---------------------------------------------------------------------------

@study_bp.route('/subscription/reorder/post', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def subscription_reorder(username: str):
    user_id = session['user_id']
    items = request.get_json(silent=True) or []
    for item in items:
        if not isinstance(item, dict):
            continue
        sub_id = item.get('subscriptionID')
        pos = item.get('position')
        if sub_id and pos is not None:
            sub = StudyModel.get_subscription_by_id(sub_id)
            if sub and sub['userID'] == user_id:
                db_manager.execute_update(
                    'UPDATE study_subscription SET position=%s WHERE subscriptionID=%s',
                    (int(pos), sub_id),
                )
    return jsonify({'status': 'ok'})


# ---------------------------------------------------------------------------
# Public RSS feed — today's study items that have audio
# ---------------------------------------------------------------------------

@study_bp.route('/feed.xml')
def feed_xml(username: str):
    user = db_manager.execute_one(
        "SELECT userID FROM `user` WHERE username = %s", (username,))
    if not user:
        return make_response('<error>User not found</error>', 404,
                             {'Content-Type': 'text/xml'})

    user_id = user['userID']
    tz_row = db_manager.execute_one(
        "SELECT value FROM user_preference WHERE userID = %s AND preference = 'timezone'",
        (user_id,))
    timezone = tz_row['value'] if tz_row else 'UTC'

    today = today_for_tz(timezone)
    subscriptions = StudyModel.get_user_subscriptions(user_id)

    seen_ids = set()
    seen_urls = set()
    sources = []
    for sub in subscriptions:
        all_sources = StudyModel.get_sources(sub['collectionID'])
        items = StudyModel.sources_for_date(sub, all_sources, today, user_id)
        for item in items:
            sid = item['sourceID']
            aurl = item.get('audio_url') or ''
            if sid not in seen_ids and aurl and aurl not in ('', 'none') and aurl not in seen_urls:
                seen_ids.add(sid)
                seen_urls.add(aurl)
                sources.append(item)
    sources = sources[:100]

    # Resolve relative audio_url paths to absolute URLs for valid RSS enclosures.
    base_url = request.url_root.rstrip('/')
    for item in sources:
        aurl = item.get('audio_url') or ''
        if aurl.startswith('/'):
            item['audio_url'] = base_url + aurl

    # Assign distinct pubDates (one day apart) so podcast apps order episodes
    # reliably. Time-staggering within a single day is ignored by some clients.
    for idx, item in enumerate(sources):
        pub_date = today - timedelta(days=idx)
        item['_pub_date'] = pub_date.strftime('%a, %d %b %Y')

    rss = render_template('study_feed.xml', username=username, today=today, sources=sources)
    response = make_response(rss)
    response.headers['Content-Type'] = 'application/rss+xml; charset=utf-8'
    return response
