"""
Book Tracker Routes
===================
Flask blueprint for all book-tracking URLs.

URL patterns
------------
GET  /<username>/book/index
POST /<username>/book/create/post
POST /<username>/book/update/post/<book_id>
POST /<username>/book/finish/post/<book_id>

Insert-only pattern
-------------------
The book table follows the insert-only pattern: updates are new rows sharing
the same bookID UUID.  Current state = MAX(id) per bookID.

Note: The schema defines `title` as NOT NULL with a UNIQUE constraint on
bookID but no NULL-sentinel delete column.  Soft-delete for books is
implemented by inserting a row with status='dismiss', which effectively hides
the book from the active lists without requiring a schema change.
"""

import uuid
from collections import defaultdict
from datetime import date, datetime

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.services.database import db_manager
from app.services.decorators import (
    PERM_BOOK,
    login_required,
    permission_required_read,
    permission_required_write,
)

book_bp = Blueprint('book', __name__)

# Valid status values matching the schema enum.
VALID_STATUSES = ('want_to_read', 'reading', 'completed', 'dismiss')

# Display order for status sections.
STATUS_ORDER = ['reading', 'want_to_read', 'completed', 'dismiss']

# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

_CURRENT_BOOKS_SQL = """
    SELECT b.bookID, b.title, b.author, b.isbn, b.pages, b.tags, b.cover,
           b.status, b.rating, b.review, b.notes, b.started, b.finished
    FROM book b
    WHERE b.userID = %s
      AND b.id = (SELECT MAX(b2.id) FROM book b2 WHERE b2.bookID = b.bookID)
      AND b.title IS NOT NULL
    ORDER BY b.created DESC
"""

_BOOK_BY_ID_SQL = """
    SELECT b.bookID, b.title, b.author, b.isbn, b.pages, b.tags, b.cover,
           b.status, b.rating, b.review, b.notes, b.started, b.finished
    FROM book b
    WHERE b.userID = %s
      AND b.bookID = %s
      AND b.id = (SELECT MAX(b2.id) FROM book b2 WHERE b2.bookID = b.bookID)
      AND b.title IS NOT NULL
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _redirect_to_index(username: str):
    """Return a redirect to the book index."""
    return redirect(url_for('book.index', username=username))


def _get_book(user_id: str, book_id: str) -> dict | None:
    """Fetch the current state of a single book; return None if not found."""
    return db_manager.execute_one(_BOOK_BY_ID_SQL, (user_id, book_id))


def _insert_book_row(book_id: str, user_id: str, title: str, author,
                     isbn, pages, tags, cover, status, rating, review,
                     notes, started, finished):
    """Insert a new book row (used for both create and update)."""
    db_manager.execute_insert(
        """
        INSERT INTO book
            (bookID, userID, title, author, isbn, pages, tags, cover,
             status, rating, review, notes, started, finished, created, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (book_id, user_id, title, author, isbn, pages, tags, cover,
         status, rating, review, notes, started, finished,
         datetime.now(), user_id),
    )


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@book_bp.route('/index')
@login_required
@permission_required_read(PERM_BOOK)
def index(username: str):
    """
    List all books, grouped by reading status.

    Template context
    ----------------
    books_by_status : dict[str, list[dict]]
        Ordered mapping of status -> list of book dicts.
    username        : str
    """
    user_id = session['user_id']
    all_books = db_manager.execute_query(_CURRENT_BOOKS_SQL, (user_id,))

    books_by_status: dict[str, list] = defaultdict(list)
    for book in all_books:
        books_by_status[book['status']].append(book)

    # Build ordered dict so template iterates in STATUS_ORDER.
    ordered: dict[str, list] = {s: books_by_status.get(s, []) for s in STATUS_ORDER}

    return render_template(
        'book_index.html',
        books_by_status=ordered,
        username=username,
    )


# ---------------------------------------------------------------------------
# POST routes (PRG pattern)
# ---------------------------------------------------------------------------

@book_bp.route('/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOK)
@permission_required_write(PERM_BOOK)
def create(username: str):
    """
    Add a new book to the tracker.

    Form fields
    -----------
    title  : str   Required.
    author : str   Optional.
    isbn   : str   Optional.
    pages  : int   Optional.
    tags   : str   Optional, comma-separated.
    status : str   One of VALID_STATUSES; defaults to 'want_to_read'.
    """
    user_id = session['user_id']
    title = request.form.get('title', '').strip()

    if not title:
        flash('Title is required.', 'error')
        return _redirect_to_index(username)

    author = request.form.get('author', '').strip() or None
    isbn = request.form.get('isbn', '').strip() or None
    pages_str = request.form.get('pages', '').strip()
    pages = int(pages_str) if pages_str.isdigit() else None
    tags = request.form.get('tags', '').strip() or None
    status = request.form.get('status', 'want_to_read')
    if status not in VALID_STATUSES:
        status = 'want_to_read'

    started = date.today() if status == 'reading' else None
    finished = date.today() if status == 'completed' else None

    book_id = str(uuid.uuid4())

    _insert_book_row(
        book_id=book_id,
        user_id=user_id,
        title=title,
        author=author,
        isbn=isbn,
        pages=pages,
        tags=tags,
        cover=None,
        status=status,
        rating=None,
        review=None,
        notes=None,
        started=started,
        finished=finished,
    )

    flash(f'"{title}" added to your book list.', 'success')
    return _redirect_to_index(username)


@book_bp.route('/update/post/<book_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOK)
@permission_required_write(PERM_BOOK)
def update(username: str, book_id: str):
    """
    Update a book's status or notes by inserting a new row (insert-only pattern).

    Form fields
    -----------
    status  : str   Optional new status.
    rating  : int   Optional 1-5 rating.
    review  : str   Optional review text.
    notes   : str   Optional personal notes.
    started : str   Optional ISO date.
    finished: str   Optional ISO date.
    """
    user_id = session['user_id']
    book = _get_book(user_id, book_id)

    if book is None:
        flash('Book not found.', 'error')
        return _redirect_to_index(username)

    status = request.form.get('status', book['status'])
    if status not in VALID_STATUSES:
        status = book['status']

    rating_str = request.form.get('rating', '').strip()
    rating = int(rating_str) if rating_str.isdigit() and 1 <= int(rating_str) <= 5 else book['rating']

    review = request.form.get('review', '').strip() or book['review']
    notes = request.form.get('notes', '').strip() or book['notes']

    started_str = request.form.get('started', '').strip()
    try:
        started = datetime.strptime(started_str, '%Y-%m-%d').date() if started_str else book['started']
    except ValueError:
        started = book['started']

    finished_str = request.form.get('finished', '').strip()
    try:
        finished = datetime.strptime(finished_str, '%Y-%m-%d').date() if finished_str else book['finished']
    except ValueError:
        finished = book['finished']

    _insert_book_row(
        book_id=book_id,
        user_id=user_id,
        title=book['title'],
        author=book['author'],
        isbn=book['isbn'],
        pages=book['pages'],
        tags=book['tags'],
        cover=book['cover'],
        status=status,
        rating=rating,
        review=review or None,
        notes=notes or None,
        started=started,
        finished=finished,
    )

    flash('Book updated.', 'success')
    return _redirect_to_index(username)


@book_bp.route('/finish/post/<book_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_BOOK)
@permission_required_write(PERM_BOOK)
def finish(username: str, book_id: str):
    """
    Mark a book as finished (status='completed', finished=today).

    Path Parameters
    ---------------
    book_id : str   The bookID UUID to finish.
    """
    user_id = session['user_id']
    book = _get_book(user_id, book_id)

    if book is None:
        flash('Book not found.', 'error')
        return _redirect_to_index(username)

    _insert_book_row(
        book_id=book_id,
        user_id=user_id,
        title=book['title'],
        author=book['author'],
        isbn=book['isbn'],
        pages=book['pages'],
        tags=book['tags'],
        cover=book['cover'],
        status='completed',
        rating=book['rating'],
        review=book['review'],
        notes=book['notes'],
        started=book['started'],
        finished=date.today(),
    )

    flash(f'"{book["title"]}" marked as finished.', 'success')
    return _redirect_to_index(username)
