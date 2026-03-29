"""
Podcast Routes
==============
Flask blueprint for podcast feed management and RSS generation.

URL patterns
------------
GET  /<username>/podcast/subscription              -> manage podcast feeds (authenticated)
POST /<username>/podcast/subscription/create/post  -> create a new podcast feed
GET  /<username>/podcast/list                      -> manage podcast lists (authenticated)
POST /<username>/podcast/list/create/post          -> create a new podcast list
GET  /<username>/podcast/feed/<feed_id>.xml        -> serve RSS feed (public, no auth)

Spec references
---------------
§5.9.3 Every user can create multiple feeds listed at /[username]/podcast/subscription
§5.9.4 Podcast lists created at /[username]/podcast/list
"""

import uuid
from datetime import datetime

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    make_response,
)

from app.services.database import db_manager
from app.services.decorators import (
    PERM_PODCAST,
    login_required,
    permission_required_read,
    permission_required_write,
)

podcast_bp = Blueprint('podcast', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_feeds(user_id: str) -> list[dict]:
    """Return all podcast feeds for a user."""
    return db_manager.execute_query(
        """
        SELECT feedID, name, description, date_from, artwork, created
        FROM podcast
        WHERE userID = %s
        ORDER BY id DESC
        """,
        (user_id,),
    )


def _get_lists() -> list[dict]:
    """Return all podcast lists."""
    return db_manager.execute_query(
        """
        SELECT listID, title, description, category, frequency, `repeat`, created
        FROM podcast_list
        ORDER BY id DESC
        """,
        (),
    )


def _get_feed_episodes(feed_id: str) -> list[dict]:
    """Return episodes for a given feed via subscription -> list -> listItem -> episode."""
    return db_manager.execute_query(
        """
        SELECT pe.title, pe.author, pe.description, pe.file_url, pe.file_size,
               pe.file_type, pe.duration, pe.artwork, pe.created, pe.episode, pe.season,
               pe.episodeID
        FROM podcast_subscription ps
        JOIN podcast_list pl ON pl.listID = ps.listID
        JOIN podcast_listItem pli ON pli.listID = pl.listID
        JOIN podcast_episode pe ON pe.episodeID = pli.episodeID
        WHERE ps.feedID = %s
        ORDER BY pe.created DESC
        """,
        (feed_id,),
    )


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@podcast_bp.route('/subscription')
@login_required
@permission_required_read(PERM_PODCAST)
def subscription(username: str):
    """
    Manage podcast feeds (listed at /[username]/podcast/subscription per spec §5.9.3).
    """
    user_id = session['user_id']
    feeds = _get_feeds(user_id)
    all_lists = _get_lists()

    return render_template(
        'podcast_subscription.html',
        feeds=feeds,
        all_lists=all_lists,
        username=username,
        area='podcast',
    )


@podcast_bp.route('/list')
@login_required
@permission_required_read(PERM_PODCAST)
def list_index(username: str):
    """
    Manage podcast lists (created at /[username]/podcast/list per spec §5.9.4).
    """
    all_lists = _get_lists()

    return render_template(
        'podcast_list.html',
        all_lists=all_lists,
        username=username,
        area='podcast',
    )


@podcast_bp.route('/feed/<feed_id>.xml')
def feed_xml(username: str, feed_id: str):
    """
    Serve an RSS feed as XML (no authentication required).

    Validates that the feed_id belongs to the username in the URL to prevent
    enumeration, but does not require a session.
    """
    feed = db_manager.execute_one(
        """
        SELECT p.feedID, p.name, p.description, p.artwork, p.created,
               u.username
        FROM podcast p
        JOIN user u ON u.userID = p.userID
        WHERE p.feedID = %s AND u.username = %s
        """,
        (feed_id, username),
    )

    if feed is None:
        return make_response('<error>Feed not found</error>', 404, {'Content-Type': 'text/xml'})

    episodes = _get_feed_episodes(feed_id)

    rss_content = render_template(
        'podcast_feed.xml',
        feed=feed,
        episodes=episodes,
        username=username,
        feed_url=request.url,
    )

    response = make_response(rss_content)
    response.headers['Content-Type'] = 'application/rss+xml; charset=utf-8'
    return response


# ---------------------------------------------------------------------------
# POST routes
# ---------------------------------------------------------------------------

@podcast_bp.route('/subscription/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_PODCAST)
@permission_required_write(PERM_PODCAST)
def subscription_create(username: str):
    """
    Create a new podcast feed.

    Form fields
    -----------
    name        : str   Required.
    description : str   Optional.
    """
    user_id = session['user_id']
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip() or None

    if not name:
        flash('Feed name is required.', 'error')
        return redirect(url_for('podcast.subscription', username=username))

    feed_id = str(uuid.uuid4())
    db_manager.execute_insert(
        """
        INSERT INTO podcast (feedID, userID, name, description, created, created_by)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (feed_id, user_id, name, description, datetime.now(), user_id),
    )

    flash(f'Feed "{name}" created.', 'success')
    return redirect(url_for('podcast.subscription', username=username))


@podcast_bp.route('/list/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_PODCAST)
@permission_required_write(PERM_PODCAST)
def list_create(username: str):
    """
    Create a new podcast list.

    Form fields
    -----------
    title       : str   Required.
    description : str   Optional.
    category    : str   Optional.
    frequency   : str   One of daily/twoperday/threeperday/fourperday/weekly.
    """
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip() or None
    category = request.form.get('category', '').strip() or None
    frequency = request.form.get('frequency', 'daily').strip()

    valid_frequencies = {'daily', 'twoperday', 'threeperday', 'fourperday', 'weekly'}
    if frequency not in valid_frequencies:
        frequency = 'daily'

    if not title:
        flash('List title is required.', 'error')
        return redirect(url_for('podcast.list_index', username=username))

    list_id = str(uuid.uuid4())
    user_id = session['user_id']
    db_manager.execute_insert(
        """
        INSERT INTO podcast_list (listID, title, description, category, frequency, `repeat`, created, created_by)
        VALUES (%s, %s, %s, %s, %s, 1, %s, %s)
        """,
        (list_id, title, description, category, frequency, datetime.now(), user_id),
    )

    flash(f'List "{title}" created.', 'success')
    return redirect(url_for('podcast.list_index', username=username))
