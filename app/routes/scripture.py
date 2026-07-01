from flask import (
    Blueprint, render_template, request, session,
    redirect, url_for, flash, jsonify,
)

from app.models.scripture_model import ScriptureModel
from app.services.scripture_lookup import lookup as scripture_text_lookup
from app.services.decorators import (
    login_required,
    permission_required_read,
    permission_required_write,
    PERM_SCRIPTURE,
)

scripture_bp = Blueprint('scripture', __name__)

_VALID_MODES = {'reference', 'familiar', 'verbatim'}
_QUALITY_MAP = {'again': 0, 'hard': 3, 'good': 4, 'easy': 5}


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@scripture_bp.route('/index')
@login_required
@permission_required_read(PERM_SCRIPTURE)
def index(username: str):
    user_id = session['user_id']
    scriptures = ScriptureModel.get_all(user_id)
    review_states = ScriptureModel.get_review_states(user_id)
    due_count = ScriptureModel.get_due_count(user_id)

    # Build a lookup: scriptureID -> {mode: review_row}
    states_by_id: dict[str, dict] = {}
    for row in review_states:
        sid = row['scriptureID']
        if sid not in states_by_id:
            states_by_id[sid] = {}
        states_by_id[sid][row['mode']] = row

    return render_template(
        'scripture_index.html',
        username=username,
        area='scripture',
        scriptures=scriptures,
        states_by_id=states_by_id,
        due_count=due_count,
    )


@scripture_bp.route('/add')
@login_required
@permission_required_read(PERM_SCRIPTURE)
def add(username: str):
    return render_template('scripture_add.html', username=username, area='scripture')


@scripture_bp.route('/edit/<scripture_id>')
@login_required
@permission_required_read(PERM_SCRIPTURE)
def edit(username: str, scripture_id: str):
    user_id = session['user_id']
    scripture = ScriptureModel.get_one(user_id, scripture_id)
    if not scripture:
        flash('Scripture not found.', 'error')
        return redirect(url_for('scripture.index', username=username))

    states = ScriptureModel.get_review_states(user_id)
    active_modes = {
        r['mode'] for r in states if r['scriptureID'] == scripture_id
    }

    return render_template(
        'scripture_edit.html',
        username=username,
        area='scripture',
        scripture=scripture,
        active_modes=active_modes,
    )


@scripture_bp.route('/review')
@login_required
@permission_required_read(PERM_SCRIPTURE)
def review(username: str):
    user_id = session['user_id']
    due = ScriptureModel.get_due_reviews(user_id)

    import json
    cards_json = json.dumps([
        {
            'scriptureID': r['scriptureID'],
            'mode':        r['mode'],
            'reference':   r['reference'],
            'text':        r['text'] or '',
            'summary':     r['summary'] or '',
        }
        for r in due
    ])

    return render_template(
        'scripture_review.html',
        username=username,
        area='scripture',
        cards_json=cards_json,
        cards=due,
        total=len(due),
    )


# ---------------------------------------------------------------------------
# Bulk add
# ---------------------------------------------------------------------------

@scripture_bp.route('/bulk')
@login_required
@permission_required_read(PERM_SCRIPTURE)
def bulk(username: str):
    return render_template('scripture_bulk.html', username=username, area='scripture')


@scripture_bp.route('/bulk/post', methods=['POST'])
@login_required
@permission_required_read(PERM_SCRIPTURE)
@permission_required_write(PERM_SCRIPTURE)
def bulk_create(username: str):
    user_id = session['user_id']
    raw = request.form.get('references', '')
    modes = [m for m in request.form.getlist('modes') if m in _VALID_MODES]

    if not modes:
        flash('Select at least one review mode.', 'error')
        return redirect(url_for('scripture.bulk', username=username))

    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if not lines:
        flash('No references provided.', 'error')
        return redirect(url_for('scripture.bulk', username=username))

    added, skipped, no_text = 0, 0, []
    for ref in lines:
        if ScriptureModel.reference_exists(user_id, ref):
            skipped += 1
            continue
        text = scripture_text_lookup(ref) or ''
        ScriptureModel.create(user_id, ref, text, '', modes)
        added += 1
        if not text:
            no_text.append(ref)

    parts = []
    if added:
        parts.append(f'Added {added} scripture{"s" if added != 1 else ""}.')
    if skipped:
        parts.append(f'{skipped} duplicate{"s" if skipped != 1 else ""} skipped.')
    if no_text:
        parts.append(f'Text not found for: {", ".join(no_text)} — add it manually.')

    category = 'warning' if no_text else ('message' if not added else 'success')
    flash(' '.join(parts) or 'Nothing to add.', category)

    return redirect(url_for('scripture.index', username=username))


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------

@scripture_bp.route('/lookup/json')
@login_required
@permission_required_read(PERM_SCRIPTURE)
def lookup(username: str):
    ref = (request.args.get('ref') or '').strip()
    if not ref:
        return jsonify({'status': 'error', 'message': 'No reference provided.'}), 400
    text = scripture_text_lookup(ref)
    if text is None:
        return jsonify({'status': 'not_found', 'message': 'Reference not found.'}), 404
    return jsonify({'status': 'ok', 'text': text})


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

@scripture_bp.route('/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_SCRIPTURE)
@permission_required_write(PERM_SCRIPTURE)
def create(username: str):
    user_id = session['user_id']
    reference = (request.form.get('reference') or '').strip()
    text      = (request.form.get('text') or '').strip()
    summary   = (request.form.get('summary') or '').strip()
    modes     = [m for m in request.form.getlist('modes') if m in _VALID_MODES]

    if not reference:
        flash('Reference is required.', 'error')
        return redirect(url_for('scripture.add', username=username))

    if not modes:
        flash('Select at least one review mode.', 'error')
        return redirect(url_for('scripture.add', username=username))

    if ScriptureModel.reference_exists(user_id, reference):
        flash(f'"{reference}" is already in your list.', 'message')
        return redirect(url_for('scripture.index', username=username))

    ScriptureModel.create(user_id, reference, text, summary, modes)
    flash(f'"{reference}" added.', 'success')
    return redirect(url_for('scripture.index', username=username))


@scripture_bp.route('/update/post/<scripture_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_SCRIPTURE)
@permission_required_write(PERM_SCRIPTURE)
def update(username: str, scripture_id: str):
    user_id = session['user_id']
    if not ScriptureModel.get_one(user_id, scripture_id):
        flash('Scripture not found.', 'error')
        return redirect(url_for('scripture.index', username=username))

    reference = (request.form.get('reference') or '').strip()
    text      = (request.form.get('text') or '').strip()
    summary   = (request.form.get('summary') or '').strip()
    modes     = [m for m in request.form.getlist('modes') if m in _VALID_MODES]

    if not reference:
        flash('Reference is required.', 'error')
        return redirect(url_for('scripture.edit', username=username,
                                scripture_id=scripture_id))

    if not modes:
        flash('Select at least one review mode.', 'error')
        return redirect(url_for('scripture.edit', username=username,
                                scripture_id=scripture_id))

    ScriptureModel.update(user_id, scripture_id, reference, text, summary, modes)
    flash(f'"{reference}" updated.', 'success')
    return redirect(url_for('scripture.index', username=username))


@scripture_bp.route('/delete/post/<scripture_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_SCRIPTURE)
@permission_required_write(PERM_SCRIPTURE)
def delete(username: str, scripture_id: str):
    user_id = session['user_id']
    scripture = ScriptureModel.get_one(user_id, scripture_id)
    if not scripture:
        flash('Scripture not found.', 'error')
        return redirect(url_for('scripture.index', username=username))

    ScriptureModel.delete(user_id, scripture_id)
    flash(f'"{scripture["reference"]}" deleted.', 'success')
    return redirect(url_for('scripture.index', username=username))


@scripture_bp.route('/review/grade/post', methods=['POST'])
@login_required
@permission_required_read(PERM_SCRIPTURE)
@permission_required_write(PERM_SCRIPTURE)
def grade(username: str):
    user_id  = session['user_id']
    is_ajax  = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    data     = request.get_json(silent=True) if is_ajax else request.form
    scripture_id = data.get('scriptureID', '')
    mode         = data.get('mode', '')
    grade_str    = data.get('grade', '')

    if mode not in _VALID_MODES or grade_str not in _QUALITY_MAP:
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'Invalid input.'}), 400
        flash('Invalid grade.', 'error')
        return redirect(url_for('scripture.review', username=username))

    if not ScriptureModel.get_one(user_id, scripture_id):
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'Not found.'}), 404
        flash('Scripture not found.', 'error')
        return redirect(url_for('scripture.review', username=username))

    quality = _QUALITY_MAP[grade_str]
    ScriptureModel.grade_review(user_id, scripture_id, mode, quality)
    if is_ajax:
        return jsonify({'status': 'ok'})
    return redirect(url_for('scripture.review', username=username))
