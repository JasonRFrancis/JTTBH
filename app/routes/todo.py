"""
Todo Routes
===========
Flask blueprint for all todo-feature URLs.

URL patterns
------------
GET  /<username>/todo/index
GET  /<username>/todo/index/<date_str>      (date_str: YYYY-MM-DD)
GET  /<username>/todo/search
GET  /<username>/todo/search/<query>

POST /<username>/todo/create/post
POST /<username>/todo/toggle/post/<todo_id>
POST /<username>/todo/update/post/<todo_id>
POST /<username>/todo/delete/post/<todo_id>
POST /<username>/todo/move/post/<todo_id>
POST /<username>/todo/reorder/post

All POST routes follow the PRG pattern: redirect to a GET after state change
with a flash message indicating success or failure.
"""

from datetime import date, datetime, timedelta

from app.services.timezone_utils import user_today

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.models.todo_model import TodoModel
from app.models.shared_list_model import SharedListModel
from app.models.user_model import User
from app.services.decorators import (
    PERM_TODO,
    login_required,
    permission_required_read,
    permission_required_write,
)

todo_bp = Blueprint('todo', __name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Human-readable display names for the fixed planning lists.
PLANNING_LISTS = {
    'next_week':    'Next Week',
    'this_month':   'This Month',
    'next_month':   'Next Month',
    'someday_soon': 'Someday Soon',
}

#: Number of blank input slots to pre-render on daily lists.
DAILY_BLANK_SLOTS = 11

#: Number of blank input slots to pre-render on custom/planning lists.
CUSTOM_BLANK_SLOTS = 5


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _parse_date(date_str: str) -> date | None:
    """Parse YYYY-MM-DD string to date object; return None on failure."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _redirect_to_index(username: str, current_date: date):
    """Return a redirect response to the index page for the given date."""
    return redirect(url_for(
        'todo.index_date',
        username=username,
        date_str=current_date.isoformat(),
    ))


def _build_index_context(user_id: str, username: str, current_date: date) -> dict:
    """
    Build the full template context for the index view.

    Performs the push-forward check, fetches all 5 daily columns,
    all 4 planning lists, and any enabled custom lists from preferences.

    Parameters
    ----------
    user_id : str
        The authenticated userID UUID.
    username : str
        The URL username segment (used for generating action URLs).
    current_date : date
        The "active" date displayed in the centre of the weekly view.

    Returns
    -------
    dict
        Complete context dict ready for render_template.
    """
    today = user_today()

    # --- Push-forward: run once per day on first page load ----------------
    push_count = 0
    if current_date == today:
        if not TodoModel.push_forward_check(user_id, today):
            push_count = TodoModel.push_forward(user_id, today)

    # --- Build 5-day window -----------------------------------------------
    # current_date sits at index 1 (second column); yesterday is index 0.
    offsets = [-1, 0, 1, 2, 3]
    daily_lists = []
    for offset in offsets:
        day = current_date + timedelta(days=offset)
        todos = TodoModel.get_daily_todos(user_id, day)
        daily_lists.append({
            'date':         day,
            'date_str':     day.isoformat(),
            'is_today':     day == today,
            'is_current':   day == current_date,
            'todos':        todos,
            'blank_slots':  max(DAILY_BLANK_SLOTS - len(todos), 1),
        })

    # --- Planning lists ---------------------------------------------------
    planning_lists = []
    for key, display_name in PLANNING_LISTS.items():
        todos = TodoModel.get_planning_todos(user_id, key)
        planning_lists.append({
            'name':         key,
            'display_name': display_name,
            'todos':        todos,
            'blank_slots':  max(CUSTOM_BLANK_SLOTS - len(todos), 1),
        })

    # --- Custom lists from user preferences --------------------------------
    all_lists = TodoModel.get_all_lists(user_id)
    custom_lists = []
    for list_name in all_lists['custom']:
        todos = TodoModel.get_custom_todos(user_id, list_name)
        custom_lists.append({
            'name':        list_name,
            'todos':       todos,
            'blank_slots': max(CUSTOM_BLANK_SLOTS - len(todos), 1),
        })

    # --- Shared lists (owner + pinned member lists) -----------------------
    try:
        shared_index_rows = SharedListModel.get_lists_for_todo_index(user_id)
        shared_lists = []
        for row in shared_index_rows:
            list_data = SharedListModel.get_list_with_items(row['listID'])
            if list_data:
                list_data['can_edit'] = bool(row['is_owner']) or row['permission'] == 'edit'
                list_data['is_owner'] = bool(row['is_owner'])
                shared_lists.append(list_data)
        pending_invite_count = len(SharedListModel.get_pending_invites(user_id))
    except Exception:
        shared_lists = []
        pending_invite_count = 0

    return {
        'username':           username,
        'current_date':       current_date,
        'today':              today,
        'daily_lists':        daily_lists,
        'planning_lists':     planning_lists,
        'custom_lists':       custom_lists,
        'push_count':         push_count,
        'shared_lists':       shared_lists,
        'pending_invite_count': pending_invite_count,
    }


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@todo_bp.route('/index')
@login_required
@permission_required_read(PERM_TODO)
def index(username: str):
    """Redirect to today's dated index URL for clean canonical URLs."""
    return redirect(url_for(
        'todo.index_date',
        username=username,
        date_str=user_today().isoformat(),
    ))


@todo_bp.route('/index/jump')
@login_required
@permission_required_read(PERM_TODO)
def index_jump(username: str):
    """
    No-JS fallback for the date picker form.

    Reads ?date_str= from the query string and redirects to the canonical
    dated index URL.  With JavaScript, todo.js handles navigation directly.
    """
    date_str = request.args.get('date_str', '').strip()
    target = _parse_date(date_str) or user_today()
    return redirect(url_for('todo.index_date', username=username, date_str=target.isoformat()))


@todo_bp.route('/index/<date_str>')
@login_required
@permission_required_read(PERM_TODO)
def index_date(username: str, date_str: str):
    """
    Main todo list view for a specific date.

    Shows a 5-column weekly view centred on *date_str*, plus planning and
    custom lists below.  On the first load of each day for the current date,
    incomplete items from yesterday are pushed forward automatically.

    URL Parameters
    --------------
    date_str : str
        ISO date string (YYYY-MM-DD).  Defaults to today if invalid.
    """
    current_date = _parse_date(date_str) or user_today()
    user_id = session['user_id']

    context = _build_index_context(user_id, username, current_date)

    if context['push_count'] > 0:
        flash(
            f"{context['push_count']} incomplete item(s) moved forward from yesterday.",
            'message',
        )

    return render_template('todo_index.html', **context)


@todo_bp.route('/search')
@login_required
@permission_required_read(PERM_TODO)
def search(username: str):
    """
    Search page.  Accepts an optional ?q= query-string parameter so the
    search form can submit via a standard HTML GET form.  Also serves as
    the landing page when no query has been entered.
    """
    query = request.args.get('q', '').strip()
    if query:
        # Redirect to the canonical path-based URL
        return redirect(url_for('todo.search_query', username=username, query=query))
    return render_template('todo_search.html', username=username, results=[], query='')


@todo_bp.route('/search/<path:query>')
@login_required
@permission_required_read(PERM_TODO)
def search_query(username: str, query: str):
    """
    Execute a search and render results.

    URL Parameters
    --------------
    query : str
        The search string embedded in the URL path.
    """
    user_id = session['user_id']
    results = TodoModel.search(user_id, query) if query.strip() else []
    return render_template(
        'todo_search.html',
        username=username,
        results=results,
        query=query,
    )


# ---------------------------------------------------------------------------
# POST routes  (PRG pattern — all redirect after state change)
# ---------------------------------------------------------------------------

@todo_bp.route('/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def create(username: str):
    """
    Create a new todo item.

    Form fields
    -----------
    title : str         Required.
    list_type : str     One of 'daily', 'custom', 'planning'.
    due : str           ISO date; required for list_type='daily'.
    list_name : str     Required for list_type='custom' and 'planning'.
    content : str       Optional Markdown body.
    position : int      Optional; defaults to max+1 for the list.
    """
    user_id    = session['user_id']
    title      = request.form.get('title', '').strip()
    list_type  = request.form.get('list_type', 'daily')
    due_str    = request.form.get('due', '')
    list_name  = request.form.get('list_name', '') or None
    content    = request.form.get('content', '').strip() or None

    # Validate title
    if not title:
        flash('Title is required.', 'error')
        return _redirect_to_index(username, user_today())

    # Parse due date for daily todos
    due = _parse_date(due_str) if due_str else None
    if list_type == 'daily' and due is None:
        due = user_today()

    # Determine position: max existing position + 1
    if list_type == 'daily' and due:
        existing = TodoModel.get_daily_todos(user_id, due)
    elif list_type == 'planning' and list_name:
        existing = TodoModel.get_planning_todos(user_id, list_name)
    elif list_type == 'custom' and list_name:
        existing = TodoModel.get_custom_todos(user_id, list_name)
    else:
        existing = []

    position = max((t['position'] for t in existing), default=-1) + 1

    TodoModel.create(
        user_id=user_id,
        title=title,
        due=due,
        list_type=list_type,
        list_name=list_name,
        position=position,
        content=content,
    )

    flash('Item added.', 'success')

    # Redirect back to the appropriate view
    if list_type == 'daily' and due:
        return _redirect_to_index(username, due)

    return _redirect_to_index(username, user_today())


@todo_bp.route('/toggle/post/<todo_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def toggle(username: str, todo_id: str):
    """
    Toggle the completion state of a todo item.

    Path Parameters
    ---------------
    todo_id : str   The todoID UUID to toggle.
    """
    user_id = session['user_id']
    todo = TodoModel.get_todo_by_id(todo_id, user_id)

    if todo is None:
        flash('Item not found.', 'error')
        return _redirect_to_index(username, user_today())

    TodoModel.toggle_complete(todo_id, user_id)

    # Redirect back to the referring page (or today's index)
    referrer = request.referrer
    if referrer:
        return redirect(referrer)

    due = todo.get('due') or user_today()
    return _redirect_to_index(username, due if isinstance(due, date) else user_today())


@todo_bp.route('/update/post/<todo_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def update(username: str, todo_id: str):
    """
    Update the title and/or content of a todo item.

    Form fields
    -----------
    title : str     Optional new title.
    content : str   Optional new content.
    """
    user_id = session['user_id']
    todo = TodoModel.get_todo_by_id(todo_id, user_id)

    if todo is None:
        flash('Item not found.', 'error')
        return _redirect_to_index(username, user_today())

    new_title   = request.form.get('title', '').strip() or None
    new_content = request.form.get('content', '').strip() or None

    # Keep current title if not provided
    if new_title is None:
        new_title = todo['title']

    TodoModel.update(
        todo_id=todo_id,
        user_id=user_id,
        title=new_title,
        content=new_content if 'content' in request.form else None,
    )

    flash('Item updated.', 'success')

    referrer = request.referrer
    if referrer:
        return redirect(referrer)

    due = todo.get('due') or user_today()
    return _redirect_to_index(username, due if isinstance(due, date) else user_today())


@todo_bp.route('/delete/post/<todo_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def delete(username: str, todo_id: str):
    """
    Soft-delete a todo item (inserts new record with title=NULL).

    Path Parameters
    ---------------
    todo_id : str   The todoID UUID to delete.
    """
    user_id = session['user_id']
    todo = TodoModel.get_todo_by_id(todo_id, user_id)

    if todo is None:
        flash('Item not found.', 'error')
        return _redirect_to_index(username, user_today())

    due = todo.get('due') or user_today()
    TodoModel.delete(todo_id, user_id)

    flash('Item deleted.', 'success')

    referrer = request.referrer
    if referrer:
        return redirect(referrer)

    return _redirect_to_index(
        username,
        due if isinstance(due, date) else user_today(),
    )


@todo_bp.route('/move/post/<todo_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def move(username: str, todo_id: str):
    """
    Move a todo item to a different date or list.

    Form fields
    -----------
    new_due : str           ISO date string; pass empty for non-daily lists.
    new_list_type : str     One of 'daily', 'custom', 'planning'.
    new_list_name : str     Required for custom/planning destinations.
    """
    user_id = session['user_id']
    todo = TodoModel.get_todo_by_id(todo_id, user_id)

    if todo is None:
        flash('Item not found.', 'error')
        return _redirect_to_index(username, user_today())

    new_due_str    = request.form.get('new_due', '').strip()
    new_list_type  = request.form.get('new_list_type', '').strip() or None
    new_list_name  = request.form.get('new_list_name', '').strip() or None

    new_due = _parse_date(new_due_str) if new_due_str else None

    TodoModel.move(
        todo_id=todo_id,
        user_id=user_id,
        new_due=new_due,
        new_list_type=new_list_type,
        new_list_name=new_list_name,
    )

    flash('Item moved.', 'success')

    # Redirect to destination date if moving to daily
    dest_date = new_due or (todo.get('due') if isinstance(todo.get('due'), date) else None) or user_today()
    return _redirect_to_index(username, dest_date)


@todo_bp.route('/reorder/post', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def reorder(username: str):
    """
    Reorder multiple todo items by updating their positions.

    Accepts a JSON body with the following structure::

        {"todos": [{"todoID": "...", "position": 0}, ...]}

    Returns a JSON response ``{"status": "ok"}`` on success, or a redirect
    for non-AJAX callers.
    """
    from flask import jsonify  # noqa: PLC0415

    user_id = session['user_id']

    try:
        data = request.get_json(force=True, silent=True) or {}
        todos = data.get('todos', [])
        if not todos:
            return jsonify({'status': 'error', 'message': 'No todos provided'}), 400

        todo_ids  = [t['todoID']  for t in todos]
        positions = [t['position'] for t in todos]

        TodoModel.reorder(user_id, todo_ids, positions)
        return jsonify({'status': 'ok'})

    except (KeyError, TypeError) as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400


# ===========================================================================
# Shared Lists
# ===========================================================================

def _shared_referrer_fallback(username: str):
    """Redirect to todo index; used as fallback when referrer is unavailable."""
    return redirect(url_for('todo.index', username=username))


# ---------------------------------------------------------------------------
# GET routes — shared lists
# ---------------------------------------------------------------------------

@todo_bp.route('/shared/invites')
@login_required
@permission_required_read(PERM_TODO)
def shared_invites(username: str):
    user_id = session['user_id']
    invites = SharedListModel.get_pending_invites(user_id)
    return render_template(
        'todo_shared_invites.html',
        username=username,
        invites=invites,
    )


@todo_bp.route('/shared/<list_id>')
@login_required
@permission_required_read(PERM_TODO)
def shared_view(username: str, list_id: str):
    user_id = session['user_id']
    if not SharedListModel.is_member(list_id, user_id):
        flash('You do not have access to that list.', 'error')
        return _shared_referrer_fallback(username)
    list_data = SharedListModel.get_list_with_items(list_id)
    if not list_data:
        flash('List not found.', 'error')
        return _shared_referrer_fallback(username)
    can_edit = SharedListModel.get_member_permission(list_id, user_id) == 'edit'
    is_owner = SharedListModel.is_owner(list_id, user_id)
    member_row = None
    if not is_owner:
        members = SharedListModel.get_members(list_id)
        member_row = next((m for m in members if m['userID'] == user_id), None)
    return render_template(
        'todo_shared_view.html',
        username=username,
        list_data=list_data,
        can_edit=can_edit,
        is_owner=is_owner,
        member_row=member_row,
    )


@todo_bp.route('/shared/<list_id>/settings')
@login_required
@permission_required_read(PERM_TODO)
def shared_settings(username: str, list_id: str):
    user_id = session['user_id']
    if not SharedListModel.is_member(list_id, user_id):
        flash('You do not have access to that list.', 'error')
        return _shared_referrer_fallback(username)
    list_data = SharedListModel.get_list(list_id)
    if not list_data:
        flash('List not found.', 'error')
        return _shared_referrer_fallback(username)
    is_owner = SharedListModel.is_owner(list_id, user_id)
    members = SharedListModel.get_members(list_id)
    member_row = None if is_owner else next(
        (m for m in members if m['userID'] == user_id), None
    )
    return render_template(
        'todo_shared_settings.html',
        username=username,
        list_data=list_data,
        is_owner=is_owner,
        members=members,
        member_row=member_row,
    )


# ---------------------------------------------------------------------------
# POST routes — list management
# ---------------------------------------------------------------------------

@todo_bp.route('/shared/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def shared_create(username: str):
    user_id = session['user_id']
    name = request.form.get('name', '').strip()
    if not name:
        flash('List name is required.', 'error')
        return _shared_referrer_fallback(username)
    list_id = SharedListModel.create_list(user_id, name)
    flash(f'Shared list "{name}" created.', 'success')
    return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))


@todo_bp.route('/shared/delete/post/<list_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def shared_delete(username: str, list_id: str):
    user_id = session['user_id']
    if not SharedListModel.is_owner(list_id, user_id):
        flash('Only the list owner can delete it.', 'error')
        return _shared_referrer_fallback(username)
    list_data = SharedListModel.get_list(list_id)
    SharedListModel.delete_list(list_id)
    flash(f'List "{list_data["name"]}" deleted.', 'success')
    return _shared_referrer_fallback(username)


@todo_bp.route('/shared/rename/post/<list_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def shared_rename(username: str, list_id: str):
    user_id = session['user_id']
    if not SharedListModel.is_owner(list_id, user_id):
        flash('Only the list owner can rename it.', 'error')
        return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))
    name = request.form.get('name', '').strip()
    if not name:
        flash('Name cannot be empty.', 'error')
        return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))
    SharedListModel.rename_list(list_id, name)
    flash('List renamed.', 'success')
    return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))


# ---------------------------------------------------------------------------
# POST routes — member management (owner actions)
# ---------------------------------------------------------------------------

@todo_bp.route('/shared/invite/post/<list_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def shared_invite(username: str, list_id: str):
    user_id = session['user_id']
    if not SharedListModel.is_owner(list_id, user_id):
        flash('Only the list owner can invite members.', 'error')
        return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))
    invite_username = request.form.get('invite_username', '').strip()
    permission = request.form.get('permission', 'view')
    if permission not in ('view', 'edit'):
        permission = 'view'
    if not invite_username:
        flash('Username is required.', 'error')
        return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))
    if invite_username == username:
        flash('You cannot invite yourself.', 'error')
        return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))
    invitee = User.find_by_username(invite_username)
    if not invitee:
        flash(f'No account found for "{invite_username}".', 'error')
        return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))
    ok = SharedListModel.invite_member(list_id, invitee.userID, permission, user_id)
    if ok:
        flash(f'Invitation sent to {invite_username}.', 'success')
    else:
        flash(f'{invite_username} is already a member or has a pending invitation.', 'error')
    return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))


@todo_bp.route('/shared/member/permission/post/<list_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def shared_member_permission(username: str, list_id: str):
    user_id = session['user_id']
    if not SharedListModel.is_owner(list_id, user_id):
        flash('Only the list owner can change permissions.', 'error')
        return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))
    member_user_id = request.form.get('member_user_id', '').strip()
    permission = request.form.get('permission', 'view')
    if permission not in ('view', 'edit'):
        permission = 'view'
    SharedListModel.update_member_permission(list_id, member_user_id, permission)
    flash('Permission updated.', 'success')
    return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))


@todo_bp.route('/shared/member/remove/post/<list_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def shared_member_remove(username: str, list_id: str):
    user_id = session['user_id']
    if not SharedListModel.is_owner(list_id, user_id):
        flash('Only the list owner can remove members.', 'error')
        return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))
    member_user_id = request.form.get('member_user_id', '').strip()
    SharedListModel.remove_member(list_id, member_user_id)
    flash('Member removed.', 'success')
    return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))


# ---------------------------------------------------------------------------
# POST routes — invitee actions
# ---------------------------------------------------------------------------

@todo_bp.route('/shared/invite/accept/post/<list_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
def shared_invite_accept(username: str, list_id: str):
    user_id = session['user_id']
    show_in_todo = request.form.get('show_in_todo') == '1'
    SharedListModel.accept_invite(list_id, user_id, show_in_todo)
    flash('Invitation accepted.', 'success')
    return redirect(url_for('todo.shared_invites', username=username))


@todo_bp.route('/shared/invite/decline/post/<list_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
def shared_invite_decline(username: str, list_id: str):
    user_id = session['user_id']
    SharedListModel.decline_invite(list_id, user_id)
    flash('Invitation declined.', 'message')
    return redirect(url_for('todo.shared_invites', username=username))


# ---------------------------------------------------------------------------
# POST routes — member self-management
# ---------------------------------------------------------------------------

@todo_bp.route('/shared/pin/post/<list_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
def shared_pin(username: str, list_id: str):
    user_id = session['user_id']
    SharedListModel.toggle_show_in_todo(list_id, user_id)
    return redirect(request.referrer or url_for('todo.shared_settings', username=username, list_id=list_id))


@todo_bp.route('/shared/leave/post/<list_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
def shared_leave(username: str, list_id: str):
    user_id = session['user_id']
    if SharedListModel.is_owner(list_id, user_id):
        flash('As the owner, you cannot leave your own list. Delete it instead.', 'error')
        return redirect(url_for('todo.shared_settings', username=username, list_id=list_id))
    SharedListModel.leave_list(list_id, user_id)
    flash('You have left the list.', 'message')
    return _shared_referrer_fallback(username)


# ---------------------------------------------------------------------------
# POST routes — item operations
# ---------------------------------------------------------------------------

@todo_bp.route('/shared/item/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def shared_item_create(username: str):
    user_id = session['user_id']
    list_id = request.form.get('list_id', '').strip()
    title = request.form.get('title', '').strip()
    if not list_id or not title:
        return redirect(request.referrer or url_for('todo.index', username=username))
    if SharedListModel.get_member_permission(list_id, user_id) != 'edit':
        flash('You do not have edit access to this list.', 'error')
        return redirect(request.referrer or url_for('todo.index', username=username))
    SharedListModel.create_item(list_id, user_id, title)
    return redirect(request.referrer or url_for('todo.index', username=username))


@todo_bp.route('/shared/item/toggle/post/<item_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def shared_item_toggle(username: str, item_id: str):
    user_id = session['user_id']
    item = SharedListModel.get_item(item_id)
    if not item:
        flash('Item not found.', 'error')
        return redirect(request.referrer or url_for('todo.index', username=username))
    if SharedListModel.get_member_permission(item['listID'], user_id) != 'edit':
        flash('You do not have edit access to this list.', 'error')
        return redirect(request.referrer or url_for('todo.index', username=username))
    SharedListModel.toggle_item(item_id, user_id)
    return redirect(request.referrer or url_for('todo.index', username=username))


@todo_bp.route('/shared/item/update/post/<item_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def shared_item_update(username: str, item_id: str):
    user_id = session['user_id']
    item = SharedListModel.get_item(item_id)
    if not item:
        return redirect(request.referrer or url_for('todo.index', username=username))
    if SharedListModel.get_member_permission(item['listID'], user_id) != 'edit':
        flash('You do not have edit access to this list.', 'error')
        return redirect(request.referrer or url_for('todo.index', username=username))
    title = request.form.get('title', '').strip()
    if title:
        SharedListModel.update_item(item_id, title, user_id)
    return redirect(request.referrer or url_for('todo.index', username=username))


@todo_bp.route('/shared/item/delete/post/<item_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def shared_item_delete(username: str, item_id: str):
    user_id = session['user_id']
    item = SharedListModel.get_item(item_id)
    if not item:
        return redirect(request.referrer or url_for('todo.index', username=username))
    if SharedListModel.get_member_permission(item['listID'], user_id) != 'edit':
        flash('You do not have edit access to this list.', 'error')
        return redirect(request.referrer or url_for('todo.index', username=username))
    SharedListModel.delete_item(item_id, user_id)
    return redirect(request.referrer or url_for('todo.index', username=username))
