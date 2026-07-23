"""
Quote Routes
============
Flask blueprint for the quote tracker.

URL patterns
------------
GET  /<username>/quote/index              list all quotes; ?tag= to filter
GET  /<username>/quote/add                add form (prefilled from query params)

POST /<username>/quote/create/post        create new quote
POST /<username>/quote/update/post/<id>   update existing quote (insert-only)
POST /<username>/quote/delete/post/<id>   soft-delete quote (insert body=NULL)
"""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.models.quote_model import QuoteModel
from app.models.topic_model import TopicModel
from app.services.decorators import (
    PERM_QUOTE,
    login_required,
    permission_required_read,
    permission_required_write,
)

quote_bp = Blueprint('quote', __name__)


@quote_bp.route('/index')
@login_required
@permission_required_read(PERM_QUOTE)
def index(username: str):
    user_id = session['user_id']
    tag = request.args.get('tag', '').strip() or None
    quotes = QuoteModel.get_all(user_id, tag=tag)
    all_tags = QuoteModel.get_all_tags(user_id)
    all_topics = TopicModel.get_all()
    return render_template(
        'quote_index.html',
        username=username,
        area='quote',
        quotes=quotes,
        all_tags=all_tags,
        all_topics=all_topics,
        active_tag=tag,
    )


@quote_bp.route('/add')
@login_required
@permission_required_read(PERM_QUOTE)
def add(username: str):
    all_tags = QuoteModel.get_all_tags(session['user_id'])
    all_topics = TopicModel.get_all()
    return render_template(
        'quote_add.html',
        username=username,
        area='quote',
        all_tags=all_tags,
        all_topics=all_topics,
        prefill={
            'text':   request.args.get('text', ''),
            'author': request.args.get('author', ''),
            'title':  request.args.get('title', ''),
            'source': request.args.get('source', ''),
        },
    )


@quote_bp.route('/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_QUOTE)
@permission_required_write(PERM_QUOTE)
def create(username: str):
    body = request.form.get('body', '').strip()
    if not body:
        flash('Quote text is required.', 'error')
        return redirect(url_for('quote.add', username=username))
    author = request.form.get('author', '').strip()
    title  = request.form.get('title', '').strip()
    source = request.form.get('source', '').strip()
    tags   = _normalise_tags(request.form.get('tags', ''))
    QuoteModel.create(session['user_id'], body, author, title, source, tags)
    flash('Quote saved.', 'success')
    return redirect(url_for('quote.index', username=username))


@quote_bp.route('/update/post/<quote_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_QUOTE)
@permission_required_write(PERM_QUOTE)
def update(username: str, quote_id: str):
    user_id = session['user_id']
    if not QuoteModel.get_one(user_id, quote_id):
        flash('Quote not found.', 'error')
        return redirect(url_for('quote.index', username=username))
    body = request.form.get('body', '').strip()
    if not body:
        flash('Quote text is required.', 'error')
        return redirect(url_for('quote.index', username=username))
    author = request.form.get('author', '').strip()
    title  = request.form.get('title', '').strip()
    source = request.form.get('source', '').strip()
    tags   = _normalise_tags(request.form.get('tags', ''))
    QuoteModel.update(user_id, quote_id, body, author, title, source, tags)
    flash('Quote updated.', 'success')
    return redirect(url_for('quote.index', username=username))


@quote_bp.route('/delete/post/<quote_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_QUOTE)
@permission_required_write(PERM_QUOTE)
def delete(username: str, quote_id: str):
    user_id = session['user_id']
    if not QuoteModel.get_one(user_id, quote_id):
        flash('Quote not found.', 'error')
        return redirect(url_for('quote.index', username=username))
    QuoteModel.delete(user_id, quote_id)
    flash('Quote deleted.', 'success')
    return redirect(url_for('quote.index', username=username))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_tags(raw: str) -> str:
    """Strip whitespace from each tag, deduplicate, return comma-joined string."""
    tags = [t.strip() for t in raw.split(',') if t.strip()]
    seen = []
    for t in tags:
        if t.lower() not in [s.lower() for s in seen]:
            seen.append(t)
    return ', '.join(seen) if seen else ''
