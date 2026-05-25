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

POST /<u>/fitness/log/set/post                     → JSON
POST /<u>/fitness/log/set/delete/post/<log_set_id> → JSON
POST /<u>/fitness/log/end/post/<log_id>

POST /<u>/fitness/weight/post  → JSON
"""

from datetime import date, datetime

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
from app.services.decorators import (
    PERM_FITNESS,
    login_required,
    permission_required_read,
    permission_required_write,
)

fitness_bp = Blueprint('fitness', __name__)

_DOW_ORDER = [1, 2, 3, 4, 5, 6]  # Mon–Sat (no Sunday)


# ─────────────────────────────────────────────────────────────────────────────
# GET routes
# ─────────────────────────────────────────────────────────────────────────────

@fitness_bp.route('/index')
@login_required
@permission_required_read(PERM_FITNESS)
def index(username: str):
    user_id = session['user_id']
    today = user_today()
    # Python weekday(): Mon=0 → day_of_week: Sun=0, Mon=1, ..., Sat=6
    day_of_week = (today.weekday() + 1) % 7

    program = FitnessModel.get_active_program(user_id)
    exercises = []
    todays_log = None
    location = None

    if program:
        exercises = FitnessModel.get_day_exercises(program['fitnessID'], day_of_week)
        todays_log = FitnessModel.get_todays_log(user_id, today)

        # Attach previous-session sets and today's sets to each exercise
        today_sets_map: dict[str, list] = {}
        if todays_log:
            for s in FitnessModel.get_log_sets(todays_log['logID']):
                today_sets_map.setdefault(s['exerciseID'], []).append(s)

        for ex in exercises:
            ex_id = ex['exerciseID']
            ex['today_sets'] = today_sets_map.get(ex_id, [])
            ex['prev_sets'] = FitnessModel.get_last_sets_for_exercise(
                user_id, ex_id, today
            )

        if exercises:
            location = exercises[0].get('location', 'gym')

    body_weight = FitnessModel.get_todays_body_weight(user_id, today)

    return render_template(
        'fitness_index.html',
        username=username,
        area='fitness',
        program=program,
        exercises=exercises,
        todays_log=todays_log,
        body_weight=body_weight,
        today=today,
        day_name=DAY_NAMES.get(day_of_week, ''),
        location=location,
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


@fitness_bp.route('/settings')
@login_required
@permission_required_read(PERM_FITNESS)
def settings(username: str):
    user_id = session['user_id']
    programs = FitnessModel.get_programs(user_id)
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
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST — program management
# ─────────────────────────────────────────────────────────────────────────────

@fitness_bp.route('/program/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def program_create(username: str):
    name = request.form.get('name', '').strip()
    if not name:
        flash('Program name is required.', 'error')
        return redirect(url_for('fitness.settings', username=username))
    description = request.form.get('description', '').strip()
    fitness_id = FitnessModel.create_program(session['user_id'], name, description)
    flash(f'"{name}" created.', 'success')
    return redirect(url_for('fitness.settings_program', username=username,
                            fitness_id=fitness_id))


@fitness_bp.route('/program/activate/post/<fitness_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def program_activate(username: str, fitness_id: str):
    FitnessModel.activate_program(session['user_id'], fitness_id)
    flash('Program activated.', 'success')
    return redirect(url_for('fitness.settings', username=username))


@fitness_bp.route('/program/delete/post/<fitness_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def program_delete(username: str, fitness_id: str):
    FitnessModel.delete_program(fitness_id, session['user_id'])
    flash('Program deleted.', 'success')
    return redirect(url_for('fitness.settings', username=username))


@fitness_bp.route('/program/exercise/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def program_exercise_create(username: str):
    f = request.form
    fitness_id = f.get('fitness_id', '').strip()
    if not fitness_id:
        flash('Missing program.', 'error')
        return redirect(url_for('fitness.settings', username=username))

    # Verify ownership
    programs = FitnessModel.get_programs(session['user_id'])
    if not any(p['fitnessID'] == fitness_id for p in programs):
        flash('Program not found.', 'error')
        return redirect(url_for('fitness.settings', username=username))

    exercise_id = f.get('exercise_id', '').strip()
    if not exercise_id:
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
    return redirect(url_for('fitness.settings_program', username=username,
                            fitness_id=fitness_id) if fitness_id
                   else url_for('fitness.settings', username=username))


@fitness_bp.route('/exercise/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def exercise_create(username: str):
    name = request.form.get('name', '').strip()
    if not name:
        flash('Exercise name is required.', 'error')
        return redirect(url_for('fitness.settings', username=username))
    FitnessModel.create_exercise(
        name=name,
        description=request.form.get('description', '').strip() or None,
        equipment_type=request.form.get('equipment_type', '').strip() or None,
        exercise_type=request.form.get('type', 'strength'),
        muscle_group=request.form.get('muscle_group', '').strip() or None,
        video_url=request.form.get('video_url', '').strip() or None,
    )
    flash(f'"{name}" added to catalog.', 'success')
    return redirect(url_for('fitness.settings', username=username))


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

    exercise_id = f.get('exercise_id', '').strip()
    if not exercise_id:
        return jsonify({'status': 'error', 'message': 'Missing exercise_id'}), 400

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

    # Auto-create today's log if needed
    program = FitnessModel.get_active_program(user_id)
    fitness_id = program['fitnessID'] if program else None
    log_id = FitnessModel.get_or_create_log(user_id, fitness_id, user_today())

    log_set_id = FitnessModel.log_set(
        log_id=log_id,
        exercise_id=exercise_id,
        set_number=set_number,
        weight=weight,
        reps=reps,
        notes=f.get('notes', '').strip() or None,
        duration=duration,
        speed=speed,
        incline=incline,
    )
    return jsonify({'status': 'ok', 'logSetID': log_set_id, 'logID': log_id})


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
    return redirect(url_for('fitness.index', username=username))


# ─────────────────────────────────────────────────────────────────────────────
# POST — body weight (JSON)
# ─────────────────────────────────────────────────────────────────────────────

@fitness_bp.route('/weight/post', methods=['POST'])
@login_required
@permission_required_read(PERM_FITNESS)
@permission_required_write(PERM_FITNESS)
def weight_post(username: str):
    user_id = session['user_id']
    try:
        weight = float(request.form.get('weight', ''))
        if weight <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid weight'}), 400

    weight_id = FitnessModel.log_body_weight(user_id, weight, user_today())
    return jsonify({'status': 'ok', 'weightID': weight_id, 'weight': weight})
