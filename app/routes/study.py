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
"""

from datetime import date, timedelta

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.models.study_model import StudyModel
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

    subscriptions = StudyModel.get_user_subscriptions(session['user_id'])

    day_sources = []
    for sub in subscriptions:
        sources = StudyModel.get_sources(sub['collectionID'])
        items = StudyModel.sources_for_date(sub, sources, target_date)
        if items:
            day_sources.append({
                'collection_name': sub['collection_name'],
                'collection_id': sub['collectionID'],
                'mode': sub['mode'],
                'sources': items,
            })

    completions = StudyModel.get_completions_for_date(session['user_id'], target_date)

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
    )


# ---------------------------------------------------------------------------
# Collections browser
# ---------------------------------------------------------------------------

@study_bp.route('/collections')
@login_required
@permission_required_read(PERM_STUDY)
def collections(username: str):
    all_collections = StudyModel.get_all_collections()
    user_subs = {s['collectionID']: s for s in StudyModel.get_user_subscriptions(session['user_id'])}
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
    existing = StudyModel.get_subscription(session['user_id'], collection_id)
    if existing:
        flash('Already subscribed.', 'warning')
        return redirect(url_for('study.collections', username=username))
    per_day_raw = request.form.get('per_day', '1').strip()
    try:
        per_day = max(1, int(per_day_raw))
    except ValueError:
        per_day = 1
    start_date_raw = request.form.get('start_date', '').strip()
    start_date = _parse_date(start_date_raw) if start_date_raw else today_for_tz(session.get('timezone', 'UTC'))
    StudyModel.create_subscription(session['user_id'], collection_id, per_day, start_date)
    flash(f'Subscribed to "{collection["name"]}".', 'success')
    return redirect(url_for('study.collections', username=username))


@study_bp.route('/subscription/update/post/<subscription_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_STUDY)
@permission_required_write(PERM_STUDY)
def subscription_update(username: str, subscription_id: str):
    sub = StudyModel.get_subscription_by_id(subscription_id)
    if not sub or sub['userID'] != session['user_id']:
        flash('Subscription not found.', 'error')
        return redirect(url_for('study.collections', username=username))
    per_day_raw = request.form.get('per_day', '1').strip()
    try:
        per_day = max(1, int(per_day_raw))
    except ValueError:
        per_day = 1
    start_date_raw = request.form.get('start_date', '').strip()
    start_date = _parse_date(start_date_raw) if start_date_raw else sub['start_date']
    StudyModel.update_subscription(subscription_id, per_day, start_date)
    flash('Subscription updated.', 'success')
    return redirect(url_for('study.collections', username=username))


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
    StudyModel.toggle_completion(session['user_id'], source_id, target_date)
    if date_str:
        return redirect(url_for('study.index', username=username, date_str=date_str))
    return redirect(url_for('study.index', username=username))
