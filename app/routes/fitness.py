"""
Fitness Routes
==============
URL patterns
------------
GET  /<u>/fitness/index                  — today's workout + body-weight entry
GET  /<u>/fitness/log                    — workout history
GET  /<u>/fitness/settings               — list / create programs
GET  /<u>/fitness/settings/<fitness_id>  — edit a program's day schedule

POST /<u>/fitness/program/create/post
POST /<u>/fitness/program/activate/post/<fitness_id>
POST /<u>/fitness/program/delete/post/<fitness_id>
POST /<u>/fitness/program/exercise/create/post
POST /<u>/fitness/program/exercise/delete/post/<program_id>
POST /<u>/fitness/program/exercise/day-toggle/post          → JSON

POST /<u>/fitness/log/set/post                     → JSON
POST /<u>/fitness/log/set/delete/post/<log_set_id> → JSON
POST /<u>/fitness/log/end/post/<log_id>

POST /<u>/fitness/weight/post  → JSON
"""

from datetime import date, datetime, timedelta

from app.services.timezone_utils import user_today

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.models.fitness_model import FitnessModel, DAY_NAMES
from app.services.database import db_manager
from app.services.decorators import (
    PERM_FITNESS,
    login_required,
    permission_required_read,
    permission_required_write,
)

fitness_bp = Blueprint('fitness', __name__)

_DOW_ORDER = [0, 1, 2, 3, 4, 5, 6]  # Sun–Sat


# ─────────────────────────────────────────────────────────────────────────────
# GET routes
# ─────────────────────────────────────────────────────────────────────────────

@fitness_bp.route('/index')
@fitness_bp.route('/index/<date_str>')
@login_required
@permission_required_read(PERM_FITNESS)
def index(username: str, date_str: str = None):
    user_id = session['user_id']
    today = user_today()

    if date_str:
        try:
            viewed_date = date.fromisoformat(date_str)
        except ValueError:
            return redirect(url_for('fitness.index', username=username))
    else:
        viewed_date = today

    # Python weekday(): Mon=0 → day_of_week: Sun=0, Mon=1, ..., Sat=6
    day_of_week = (viewed_date.weekday() + 1) % 7
    prev_date = viewed_date - timedelta(days=1)
    next_date = viewed_date + timedelta(days=1)

    program = FitnessModel.get_active_program(user_id)
    exercises = []
    todays_log = None
    location = None

    if program:
        exercises = FitnessModel.get_day_exercises(program['fitnessID'], day_of_week)
        todays_log = FitnessModel.get_todays_log(user_id, viewed_date)

        # Attach previous-session sets and today's sets to each exercise
        today_sets_map: dict[str, list] = {}
        if todays_log:
            for s in FitnessModel.get_log_sets(todays_log['logID']):
                today_sets_map.setdefault(s['exerciseID'], []).append(s)

        for ex in exercises:
            ex_id = ex['exerciseID']
            ex['today_sets'] = today_sets_map.get(ex_id, [])
            ex['prev_sets'] = FitnessModel.get_last_sets_for_exercise(
                user_id, ex_id, viewed_date
            )

        if exercises:
            location = exercises[0].get('location', 'gym')

    body_weight = FitnessModel.get_todays_body_weight(user_id, viewed_date)

    weight_days_row = db_manager.execute_one(
        "SELECT value FROM user_preference WHERE userID = %s AND preference = 'fitness_weight_days' ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    weight_days = set(weight_days_row['value'].split(',')) if weight_days_row and weight_days_row['value'] else None

    return render_template(
        'fitness_index.html',
        username=username,
        area='fitness',
        program=program,
        exercises=exercises,
        todays_log=todays_log,
        body_weight=body_weight,
        today=today,
        viewed_date=viewed_date,
        prev_date=prev_date,
        next_date=next_date,
        day_name=DAY_NAMES.get(day_of_week, ''),
        location=location,
        day_of_week=day_of_week,
        weight_days=weight_days,
    )


@fitness_bp.route('/log')
@login_required
@permission_required_read(PERM_FITNESS)
def log(username: str):
    user_id = session['user_id']
    logs = FitnessModel.get_recent_logs(user_id)

    # Attach sets to each log entry
    for entry in logs:
        sets = FitnessModel.get_log_sets(entry['logID'])
        # Group by exercise
        by_exercise: dict[str, dict] = {}
        for s in sets:
            eid = s['exerciseID']
            if eid not in by_exercise:
                by_exercise[eid] = {'name': s['exercise_name'],
                                    'type': s['exercise_type'], 'sets': []}
            by_exercise[eid]['sets'].append(s)
        entry['exercises'] = list(by_exercise.values())

    weight_history = FitnessModel.get_weight_history(user_id)

    return render_template(
        'fitness_log.html',
        username=username,
        area='fitness',
        logs=logs,
        weight_history=weight_history,
    )


@fitness_bp.route('/exercises')
@login_required
@permission_required_read(PERM_FITNESS)
def exercises(username: str):
    user_id = session['user_id']
    program = FitnessModel.get_active_program(user_id)
    if program:
        exercises_list = FitnessModel.get_exercises_with_program_days(program['fitnessID'])
        schedule = FitnessModel.get_program_schedule(program['fitnessID'])
    else:
        raw = FitnessModel.get_exercise_catalog()
        exercises_list = [{**ex, 'days': []} for ex in raw]
        schedule = None
    return render_template(
        'fitness_exercises.html',
        username=username,
        area='fitness',
        exercises=exercises_list,
        program=program,
        schedule=schedule,
        dow_order=_DOW_ORDER,
        day_names=DAY_NAMES,
    )


@fitness_bp.route('/settings')
@login_required
@permission_required_read(PERM_FITNESS)
def settings(username: str):
    user_id = session['user_id']
    programs = FitnessModel.get_programs(user_id)
    weight_days_row = db_manager.execute_one(
        "SELECT value FROM user_preference WHERE userID = %s AND preference = 'fitness_weight_days' ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    weight_days = set(weight_days_row['value'].split(',')) if weight_days_row and weight_days_row['value'] else None
    return render_template(
        'fitness_settings.html',
        username=username,
        area='fitness',
        programs=programs,
        selected=None,
        schedule=None,
        catalog=None,
        dow_order=_DOW_ORDER,
        day_names=DAY_NAMES,
        weight_days=weight_days,
    )


@fitness_bp.route('/settings/<fitness_id>')
@login_required
@permission_required_read(PERM_FITNESS)
def settings_program(username: str, fitness_id: str):
    user_id = session['user_id']
    programs = FitnessModel.get_programs(user_id)

    # Verify ownership
    selected = next((p for p in programs if p['fitnessID'] == fitness_id), None)
    if not selected:
        flash('Program not found.', 'error')
        return redirect(url_for('fitness.settings', username=username))

    schedule = FitnessModel.get_program_schedule(fitness_id)
    catalog = FitnessModel.get_exercise_catalog()
    weight_days_row = db_manager.execute_one(
        "SELECT value FROM user_preference WHERE userID = %s AND preference = 'fitness_weight_days' ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    weight_days = set(weight_days_row['value'].split(',')) if weight_days_row and weight_days_row['value'] else None

    return render_template(
        'fitness_settings.html',
        username=username,
        area='fitness',
        programs=programs,
        selected=selected,
        schedule=schedule,
        catalog=catalog,
        dow_order=_DOW_ORDER,
        day_names=DAY_NAMES,
        weight_days=weight_days,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST — program management
# ─────────────────────────────────────────────────────────────────────────────

@fitness_bp.route('/program/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def program_create(username: str):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    name = request.form.get('name', '').strip()
    if not name:
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'Program name is required.'}), 400
        flash('Program name is required.', 'error')
        return redirect(url_for('fitness.settings', username=username))
    description = request.form.get('description', '').strip()
    fitness_id = FitnessModel.create_program(session['user_id'], name, description)
    flash(f'"{name}" created.', 'success')
    if is_ajax:
        return jsonify({'status': 'ok', 'fitness_id': fitness_id})
    return redirect(url_for('fitness.settings_program', username=username,
                            fitness_id=fitness_id))


@fitness_bp.route('/program/activate/post/<fitness_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def program_activate(username: str, fitness_id: str):
    FitnessModel.activate_program(session['user_id'], fitness_id)
    flash('Program activated.', 'success')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'ok'})
    return redirect(url_for('fitness.settings', username=username))


@fitness_bp.route('/program/delete/post/<fitness_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def program_delete(username: str, fitness_id: str):
    FitnessModel.delete_program(fitness_id, session['user_id'])
    flash('Program deleted.', 'success')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'ok'})
    return redirect(url_for('fitness.settings', username=username))


@fitness_bp.route('/program/exercise/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def program_exercise_create(username: str):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    f = request.form
    fitness_id = f.get('fitness_id', '').strip()
    if not fitness_id:
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'Missing program.'}), 400
        flash('Missing program.', 'error')
        return redirect(url_for('fitness.settings', username=username))

    # Verify ownership
    programs = FitnessModel.get_programs(session['user_id'])
    if not any(p['fitnessID'] == fitness_id for p in programs):
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'Program not found.'}), 404
        flash('Program not found.', 'error')
        return redirect(url_for('fitness.settings', username=username))

    exercise_id = f.get('exercise_id', '').strip()
    if not exercise_id:
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'Exercise is required.'}), 400
        flash('Exercise is required.', 'error')
        return redirect(url_for('fitness.settings_program', username=username,
                                fitness_id=fitness_id))

    try:
        day_of_week = int(f.get('day_of_week', 1))
    except (TypeError, ValueError):
        day_of_week = 1

    location = f.get('location', 'gym')
    notes = f.get('notes', '').strip() or None

    def _int(val):
        try:
            v = int(val)
            return v if v > 0 else None
        except (TypeError, ValueError):
            return None

    def _float(val):
        try:
            v = float(val)
            return v if v > 0 else None
        except (TypeError, ValueError):
            return None

    # Determine order_index = max + 1 for this day
    existing = FitnessModel.get_day_exercises(fitness_id, day_of_week)
    order_index = (max((e['order_index'] for e in existing), default=0) + 1)

    FitnessModel.add_program_exercise(
        fitness_id=fitness_id,
        day_of_week=day_of_week,
        exercise_id=exercise_id,
        location=location,
        sets=_int(f.get('sets')),
        reps=_int(f.get('reps')),
        weight=_float(f.get('weight')),
        notes=notes,
        order_index=order_index,
        duration=_int(f.get('duration')),
        speed=_float(f.get('speed')),
        incline=_float(f.get('incline')),
    )
    flash('Exercise added.', 'success')
    if is_ajax:
        return jsonify({'status': 'ok'})
    return redirect(url_for('fitness.settings_program', username=username,
                            fitness_id=fitness_id))


@fitness_bp.route('/program/exercise/update/post/<program_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def program_exercise_update(username: str, program_id: str):
    fitness_id = request.form.get('fitness_id', '').strip()
    f = request.form

    def _int(val):
        try:
            v = int(val)
            return v if v > 0 else None
        except (TypeError, ValueError):
            return None

    def _float(val):
        try:
            v = float(val)
            return v if v > 0 else None
        except (TypeError, ValueError):
            return None

    FitnessModel.update_program_exercise(
        program_id=program_id,
        sets=_int(f.get('sets')),
        reps=_int(f.get('reps')),
        weight=_float(f.get('weight')),
        notes=f.get('notes', '').strip() or None,
        location=f.get('location', 'gym'),
        duration=_int(f.get('duration')),
        speed=_float(f.get('speed')),
        incline=_float(f.get('incline')),
    )
    exercise_id = f.get('exercise_id', '').strip()
    if exercise_id:
        FitnessModel.update_exercise_video(
            exercise_id, f.get('video_url', '').strip() or None
        )
    flash('Exercise updated.', 'success')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'ok'})
    return redirect(
        url_for('fitness.settings_program', username=username, fitness_id=fitness_id)
        if fitness_id else url_for('fitness.settings', username=username)
    )


@fitness_bp.route('/program/exercise/delete/post/<program_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def program_exercise_delete(username: str, program_id: str):
    fitness_id = request.form.get('fitness_id', '').strip()
    FitnessModel.delete_program_exercise(program_id, session['user_id'])
    flash('Exercise removed.', 'success')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'ok'})
    return redirect(url_for('fitness.settings_program', username=username,
                            fitness_id=fitness_id) if fitness_id
                   else url_for('fitness.settings', username=username))


@fitness_bp.route('/program/exercise/day-toggle/post', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def program_exercise_day_toggle(username: str):
    """Toggle whether an exercise is scheduled on a given day of the active program."""
    user_id = session['user_id']
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    f = request.form

    exercise_id = f.get('exercise_id', '').strip()
    try:
        day_of_week = int(f.get('day_of_week'))
    except (TypeError, ValueError):
        day_of_week = None

    if not exercise_id or day_of_week not in _DOW_ORDER:
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'Invalid request.'}), 400
        flash('Invalid request.', 'error')
        return redirect(url_for('fitness.exercises', username=username))

    program = FitnessModel.get_active_program(user_id)
    if not program:
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'No active program.'}), 400
        flash('No active program.', 'error')
        return redirect(url_for('fitness.exercises', username=username))

    fitness_id = program['fitnessID']
    day_exercises = FitnessModel.get_day_exercises(fitness_id, day_of_week)
    existing = next((e for e in day_exercises if e['exerciseID'] == exercise_id), None)

    if existing:
        FitnessModel.delete_program_exercise(existing['programID'], user_id)
        assigned = False
    else:
        order_index = max((e['order_index'] for e in day_exercises), default=0) + 1
        FitnessModel.add_program_exercise(
            fitness_id=fitness_id, day_of_week=day_of_week, exercise_id=exercise_id,
            location='gym', sets=None, reps=None, weight=None, notes=None,
            order_index=order_index, duration=None, speed=None, incline=None,
        )
        assigned = True

    if is_ajax:
        return jsonify({'status': 'ok', 'assigned': assigned})
    flash('Schedule updated.', 'success')
    return redirect(url_for('fitness.exercises', username=username))


@fitness_bp.route('/exercise/update/post/<exercise_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def exercise_update(username: str, exercise_id: str):
    name = request.form.get('name', '').strip()
    if not name:
        flash('Exercise name is required.', 'error')
        return redirect(url_for('fitness.exercises', username=username))
    FitnessModel.update_exercise(
        exercise_id=exercise_id,
        name=name,
        description=request.form.get('description', '').strip() or None,
        equipment_type=request.form.get('equipment_type', 'other'),
        exercise_type=request.form.get('type', 'machine'),
        muscle_group=request.form.get('muscle_group', '').strip() or None,
        video_url=request.form.get('video_url', '').strip() or None,
    )
    flash(f'"{name}" updated.', 'success')
    return redirect(url_for('fitness.exercises', username=username))


@fitness_bp.route('/exercise/delete/post/<exercise_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def exercise_delete(username: str, exercise_id: str):
    FitnessModel.delete_exercise(exercise_id)
    flash('Exercise deleted.', 'success')
    return redirect(url_for('fitness.exercises', username=username))


@fitness_bp.route('/program/exercise/move/post/<program_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def program_exercise_move(username: str, program_id: str):
    fitness_id = request.form.get('fitness_id', '').strip()
    direction = request.form.get('direction', '').strip()
    if direction not in ('up', 'down'):
        flash('Invalid direction.', 'error')
        return redirect(url_for('fitness.exercises', username=username))
    FitnessModel.move_program_exercise(fitness_id, program_id, direction)
    return redirect(url_for('fitness.exercises', username=username))


@fitness_bp.route('/exercise/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def exercise_create(username: str):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    name = request.form.get('name', '').strip()
    if not name:
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'Exercise name is required.'}), 400
        flash('Exercise name is required.', 'error')
        return redirect(url_for('fitness.settings', username=username))
    FitnessModel.create_exercise(
        name=name,
        description=request.form.get('description', '').strip() or None,
        equipment_type=request.form.get('equipment_type', '').strip() or None,
        exercise_type=request.form.get('type', 'machine'),
        muscle_group=request.form.get('muscle_group', '').strip() or None,
        video_url=request.form.get('video_url', '').strip() or None,
    )
    flash(f'"{name}" added to catalog.', 'success')
    if is_ajax:
        return jsonify({'status': 'ok'})
    return redirect(url_for('fitness.exercises', username=username))


# ─────────────────────────────────────────────────────────────────────────────
# POST — workout logging (JSON responses for AJAX)
# ─────────────────────────────────────────────────────────────────────────────

@fitness_bp.route('/log/set/post', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def log_set(username: str):
    user_id = session['user_id']
    f = request.form

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    exercise_id = f.get('exercise_id', '').strip()
    if not exercise_id:
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'Missing exercise_id'}), 400
        flash('Missing exercise.', 'error')
        return redirect(url_for('fitness.index', username=username))

    def _int(v):
        try:
            return int(v) if v else None
        except (TypeError, ValueError):
            return None

    def _float(v):
        try:
            return float(v) if v else None
        except (TypeError, ValueError):
            return None

    set_number = _int(f.get('set_number')) or 1
    weight = _float(f.get('weight'))
    reps = _int(f.get('reps'))
    duration = _int(f.get('duration'))
    speed = _float(f.get('speed'))
    incline = _float(f.get('incline'))

    log_date_str = f.get('log_date', '')
    try:
        log_date = date.fromisoformat(log_date_str)
    except (ValueError, AttributeError):
        log_date = user_today()

    # Auto-create the log entry for the target date if needed
    program = FitnessModel.get_active_program(user_id)
    fitness_id = program['fitnessID'] if program else None
    log_id = FitnessModel.get_or_create_log(user_id, fitness_id, log_date)

    log_set_id = FitnessModel.log_set(
        log_id=log_id,
        exercise_id=exercise_id,
        set_number=set_number,
        weight=weight,
        reps=reps,
        notes=f.get('notes', '').strip() or None,
        setup=f.get('setup', '').strip() or None,
        duration=duration,
        speed=speed,
        incline=incline,
    )

    if is_ajax:
        return jsonify({'status': 'ok', 'logSetID': log_set_id, 'logID': log_id})

    return redirect(url_for('fitness.index', username=username, date_str=log_date.isoformat()))


@fitness_bp.route('/log/set/delete/post/<log_set_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def log_set_delete(username: str, log_set_id: str):
    FitnessModel.delete_log_set(log_set_id)
    return jsonify({'status': 'ok'})


@fitness_bp.route('/log/end/post/<log_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def log_end(username: str, log_id: str):
    FitnessModel.end_workout(log_id)
    flash('Workout finished.', 'success')
    log_date_str = request.form.get('log_date', '')
    try:
        log_date = date.fromisoformat(log_date_str)
    except (ValueError, AttributeError):
        log_date = user_today()
    if log_date == user_today():
        return redirect(url_for('fitness.index', username=username))
    return redirect(url_for('fitness.index', username=username,
                            date_str=log_date.isoformat()))


@fitness_bp.route('/log/notes/post', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def log_notes_post(username: str):
    user_id = session['user_id']
    log_date_str = request.form.get('log_date', '')
    notes = request.form.get('notes', '').strip()
    try:
        log_date = date.fromisoformat(log_date_str)
    except (ValueError, AttributeError):
        log_date = user_today()
    program = FitnessModel.get_active_program(user_id)
    fitness_id = program['fitnessID'] if program else None
    log_id = FitnessModel.get_or_create_log(user_id, fitness_id, log_date)
    # Insert a new row with updated notes (insert-only pattern)
    db_manager.execute_insert("""
        INSERT INTO fitness_log
          (logID, userID, fitnessID, log_date, start_time, end_time, location, notes, created)
        SELECT logID, userID, fitnessID, log_date, start_time, end_time, location, %s, NOW()
        FROM fitness_log
        WHERE logID = %s
          AND id = (SELECT MAX(id) FROM fitness_log fl2 WHERE fl2.logID = %s)
    """, (notes or None, log_id, log_id))
    flash('Notes saved.', 'success')
    if log_date == user_today():
        return redirect(url_for('fitness.index', username=username))
    return redirect(url_for('fitness.index', username=username, date_str=log_date.isoformat()))


# ─────────────────────────────────────────────────────────────────────────────
# POST — body weight (JSON)
# ─────────────────────────────────────────────────────────────────────────────

@fitness_bp.route('/weight-schedule/post', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def weight_schedule_post(username: str):
    user_id = session['user_id']
    days = request.form.getlist('weight_day')  # list of '0'-'6' values
    value = ','.join(sorted(days))
    existing = db_manager.execute_one(
        "SELECT id FROM user_preference WHERE userID = %s AND preference = 'fitness_weight_days'",
        (user_id,)
    )
    if existing:
        db_manager.execute_update(
            "UPDATE user_preference SET value = %s WHERE userID = %s AND preference = 'fitness_weight_days'",
            (value, user_id)
        )
    else:
        db_manager.execute_insert(
            "INSERT INTO user_preference (userID, preference, value, created, created_by) VALUES (%s, %s, %s, NOW(), %s)",
            (user_id, 'fitness_weight_days', value, user_id)
        )
    flash('Weight schedule saved.', 'success')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'ok'})
    return redirect(url_for('fitness.settings', username=username))


@fitness_bp.route('/weight/post', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def weight_post(username: str):
    user_id = session['user_id']
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        weight = float(request.form.get('weight', ''))
        if weight <= 0:
            raise ValueError
    except (TypeError, ValueError):
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'Invalid weight'}), 400
        flash('Invalid weight.', 'error')
        return redirect(url_for('fitness.index', username=username))

    log_date_str = request.form.get('log_date', '')
    try:
        log_date = date.fromisoformat(log_date_str)
    except (ValueError, AttributeError):
        log_date = user_today()

    weight_id = FitnessModel.log_body_weight(user_id, weight, log_date)

    if is_ajax:
        return jsonify({'status': 'ok', 'weightID': weight_id, 'weight': weight})

    flash(f'{weight} lbs recorded.', 'success')
    return redirect(url_for('fitness.index', username=username, date_str=log_date.isoformat()))
