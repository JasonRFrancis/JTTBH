from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from app.models.meal_model import FoodModel, MealModel, sum_macros
from app.models.recipe_model import RecipeModel
from app.services import off_client
from app.services.decorators import (
    PERM_MEAL,
    login_required,
    permission_required_read,
    permission_required_write,
)
from app.services.timezone_utils import user_today

meal_bp = Blueprint('meal', __name__)

MEAL_NAMES = ('Breakfast', 'Lunch', 'Dinner', 'Snack')


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@meal_bp.route('/index')
@login_required
@permission_required_read(PERM_MEAL)
def index(username: str):
    return redirect(url_for('meal.day', username=username, day=user_today().isoformat()))


@meal_bp.route('/day/<day>')
@login_required
@permission_required_read(PERM_MEAL)
def day(username: str, day: str):
    d = _parse_day(day)
    meals = MealModel.get_day(session['user_id'], d)
    now = datetime.now(ZoneInfo(session.get('timezone') or 'UTC'))
    return render_template(
        'meal_day.html', username=username, area='meal', day=d, meals=meals,
        totals=sum_macros(m['totals'] for m in meals),
        recipes=sorted(RecipeModel.get_recipes(session['user_id']), key=lambda r: r['title'].lower()),
        meal_names=MEAL_NAMES, default_time=now.strftime('%H:%M'),
        prev_day=d - timedelta(days=1), next_day=d + timedelta(days=1), today=user_today(),
    )


@meal_bp.route('/food/<meal_id>')
@login_required
@permission_required_read(PERM_MEAL)
def food(username: str, meal_id: str):
    meal = MealModel.get_meal(meal_id, session['user_id']) or abort(404)
    q = request.args.get('q', '').strip()
    results, off_error = FoodModel.search(session['user_id'], q) if q else ([], None)
    return render_template('meal_food.html', username=username, area='meal', meal=meal, q=q,
                           results=results, off_error=off_error, is_barcode=q.isdigit() and 8 <= len(q) <= 14)


@meal_bp.route('/food/new')
@login_required
@permission_required_read(PERM_MEAL)
def food_new(username: str):
    food = dict.fromkeys(('brand', 'serving_g') + tuple(off_client.NUTRIENTS))
    food.update(code=request.args.get('code', ''), name=request.args.get('name', ''))
    return render_template('meal_food_form.html', username=username, area='meal', food=food,
                           meal_id=request.args.get('meal_id', ''), mode='new')


@meal_bp.route('/food/contribute/<food_id>')
@login_required
@permission_required_read(PERM_MEAL)
def food_contribute(username: str, food_id: str):
    food = _editable_food(food_id)
    return render_template('meal_food_form.html', username=username, area='meal', food=food,
                           meal_id=request.args.get('meal_id', ''), mode='contribute')


@meal_bp.route('/food/mine')
@login_required
@permission_required_read(PERM_MEAL)
def food_mine(username: str):
    return render_template('meal_food_mine.html', username=username, area='meal',
                           foods=FoodModel.get_custom(session['user_id']))


@meal_bp.route('/food/edit/<food_id>')
@login_required
@permission_required_read(PERM_MEAL)
def food_edit(username: str, food_id: str):
    food = _own_custom_food(food_id)
    return render_template('meal_food_form.html', username=username, area='meal', food=food,
                           meal_id=request.args.get('meal_id', ''), mode='edit')


# ---------------------------------------------------------------------------
# POST — meals
# ---------------------------------------------------------------------------

@meal_bp.route('/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_MEAL)
@permission_required_write(PERM_MEAL)
def create(username: str):
    name, eaten_at = _meal_form()
    if not name or not eaten_at:
        flash('Meal name and time are required.', 'error')
    else:
        MealModel.save_meal(session['user_id'], name, eaten_at)
        flash(f'{name} added.', 'success')
    return redirect(url_for('meal.day', username=username, day=request.form.get('day') or user_today().isoformat()))


@meal_bp.route('/update/post/<meal_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_MEAL)
@permission_required_write(PERM_MEAL)
def update(username: str, meal_id: str):
    meal = MealModel.get_meal(meal_id, session['user_id']) or abort(404)
    name, eaten_at = _meal_form()
    if not name or not eaten_at:
        flash('Meal name and time are required.', 'error')
    else:
        MealModel.save_meal(session['user_id'], name, eaten_at, meal_id=meal_id)
        flash('Meal updated.', 'success')
    return redirect(url_for('meal.day', username=username, day=(eaten_at or meal['eaten_at']).date().isoformat()))


@meal_bp.route('/delete/post/<meal_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_MEAL)
@permission_required_write(PERM_MEAL)
def delete(username: str, meal_id: str):
    meal = MealModel.get_meal(meal_id, session['user_id']) or abort(404)
    MealModel.delete_meal(meal_id, session['user_id'], meal['eaten_at'])
    flash(f"{meal['name']} deleted.", 'success')
    return redirect(url_for('meal.day', username=username, day=meal['eaten_at'].date().isoformat()))


# ---------------------------------------------------------------------------
# POST — items
# ---------------------------------------------------------------------------

@meal_bp.route('/item/create/post/<meal_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_MEAL)
@permission_required_write(PERM_MEAL)
def item_create(username: str, meal_id: str):
    user_id = session['user_id']
    meal = MealModel.get_meal(meal_id, user_id) or abort(404)
    back = url_for('meal.day', username=username, day=meal['eaten_at'].date().isoformat())

    if request.form.get('recipeID'):
        recipe = RecipeModel.get_recipe(request.form['recipeID'], user_id)
        servings = _positive(request.form.get('servings'), 1)
        if not recipe:
            flash('Recipe not found.', 'error')
            return redirect(back)
        _, unlinked = MealModel.add_recipe(user_id, meal_id, recipe, servings)
        if unlinked:
            flash(f"Added {recipe['title']}, but {len(unlinked)} ingredient(s) aren't linked to foods "
                  f"so the macros are low: {', '.join(unlinked)}.", 'warning')
        else:
            flash(f"Added {recipe['title']}.", 'success')
        return redirect(back)

    food = FoodModel.get(request.form.get('foodID', ''))
    grams = _positive(request.form.get('grams'), None)
    if not food or not grams:
        flash('Pick a food and enter grams.', 'error')
        return redirect(request.referrer or back)
    MealModel.add_food(user_id, meal_id, food, grams)
    flash(f"Added {grams:g} g {food['name']}.", 'success')
    return redirect(back)


@meal_bp.route('/item/update/post/<item_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_MEAL)
@permission_required_write(PERM_MEAL)
def item_update(username: str, item_id: str):
    quantity = _positive(request.form.get('quantity'), None)
    if not quantity:
        flash('Enter an amount greater than zero.', 'error')
        return redirect(request.referrer or url_for('meal.index', username=username))
    meal_id = MealModel.update_item(item_id, session['user_id'], quantity)
    if not meal_id:
        abort(404)
    meal = MealModel.get_meal(meal_id, session['user_id'])
    day_str = meal['eaten_at'].date().isoformat() if meal else user_today().isoformat()
    return redirect(url_for('meal.day', username=username, day=day_str))


@meal_bp.route('/item/delete/post/<item_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_MEAL)
@permission_required_write(PERM_MEAL)
def item_delete(username: str, item_id: str):
    meal_id = MealModel.delete_item(item_id, session['user_id'])
    if not meal_id:
        abort(404)
    meal = MealModel.get_meal(meal_id, session['user_id'])
    day_str = meal['eaten_at'].date().isoformat() if meal else user_today().isoformat()
    return redirect(url_for('meal.day', username=username, day=day_str))


# ---------------------------------------------------------------------------
# POST — foods / Open Food Facts contributions
# ---------------------------------------------------------------------------

@meal_bp.route('/food/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_MEAL)
@permission_required_write(PERM_MEAL)
def food_create(username: str):
    data = _food_form()
    meal_id = request.form.get('meal_id', '')
    if not data['name']:
        flash('Name is required.', 'error')
        return redirect(url_for('meal.food_new', username=username, code=data['code'] or '', meal_id=meal_id))
    if data['code'] and _code_taken(data['code']):
        flash('A food with that barcode already exists. Correct it with "Fix on Open Food Facts" instead.', 'error')
        return redirect(url_for('meal.food_new', username=username, code=data['code'], name=data['name'], meal_id=meal_id))
    FoodModel.create_custom(session['user_id'], data)
    msg, cat = f"Saved {data['name']}.", 'success'
    if request.form.get('contribute') and data['code']:
        try:
            off_client.contribute(data)
            msg += ' Also sent to Open Food Facts — thanks!'
        except Exception as e:  # noqa: BLE001
            msg, cat = msg + f' Sending to Open Food Facts failed: {e}', 'warning'
    flash(msg, cat)
    if meal_id:
        return redirect(url_for('meal.food', username=username, meal_id=meal_id, q=data['code'] or data['name']))
    return redirect(url_for('meal.index', username=username))


@meal_bp.route('/food/update/post/<food_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_MEAL)
@permission_required_write(PERM_MEAL)
def food_update(username: str, food_id: str):
    food = _own_custom_food(food_id)
    data = _food_form()
    meal_id = request.form.get('meal_id', '')
    if not data['name']:
        flash('Name is required.', 'error')
    elif data['code'] and data['code'] != food['code'] and FoodModel.get_by_code(data['code']):
        flash('Another saved food already has that barcode.', 'error')
    else:
        FoodModel.update(food_id, data)
        flash(f"Saved {data['name']}. Meals you already logged keep their old numbers.", 'success')
        return redirect(url_for('meal.food_mine', username=username))
    return redirect(url_for('meal.food_edit', username=username, food_id=food_id, meal_id=meal_id))


@meal_bp.route('/food/contribute/post/<food_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_MEAL)
@permission_required_write(PERM_MEAL)
def food_contribute_post(username: str, food_id: str):
    food = _editable_food(food_id)
    data = _food_form()
    meal_id = request.form.get('meal_id', '')
    if not data['code'] or not data['name']:
        flash('Barcode and name are required to contribute.', 'error')
        return redirect(url_for('meal.food_contribute', username=username, food_id=food_id, meal_id=meal_id))
    if data['code'] != food['code'] and FoodModel.get_by_code(data['code']):
        flash('Another saved food already has that barcode.', 'error')
        return redirect(url_for('meal.food_contribute', username=username, food_id=food_id, meal_id=meal_id))
    try:
        off_client.contribute(data)
    except Exception as e:  # noqa: BLE001
        flash(f'Open Food Facts rejected the update: {e}', 'error')
        return redirect(url_for('meal.food_contribute', username=username, food_id=food_id, meal_id=meal_id))
    FoodModel.update(food_id, data)
    flash(f"Sent {data['name']} to Open Food Facts — thanks!", 'success')
    if meal_id:
        return redirect(url_for('meal.food', username=username, meal_id=meal_id, q=data['code']))
    return redirect(url_for('meal.index', username=username))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_day(s: str) -> date:
    try:
        return date.fromisoformat(s)
    except ValueError:
        abort(404)


def _meal_form() -> tuple[str, datetime | None]:
    name = request.form.get('name', '').strip()[:100]
    try:
        eaten_at = datetime.fromisoformat(f"{request.form.get('day', '')}T{request.form.get('time', '')}")
    except ValueError:
        eaten_at = None
    return name, eaten_at


def _positive(v, default):
    try:
        f = float(v)
        return f if f > 0 else default
    except (TypeError, ValueError):
        return default


def _food_form() -> dict:
    f = request.form
    data = {
        'code': ''.join(ch for ch in f.get('code', '') if ch.isdigit()) or None,
        'name': f.get('name', '').strip()[:500],
        'brand': f.get('brand', '').strip()[:255] or None,
        'serving_g': _positive(f.get('serving_g'), None),
    }
    for col in off_client.NUTRIENTS:
        v = f.get(col, '').strip()
        try:
            data[col] = float(v) if v else None
        except ValueError:
            data[col] = None
    if data['sodium'] is not None:
        data['sodium'] = data['sodium'] / 1000  # form takes mg; OFF and `food` store g
    return data


def _code_taken(code: str) -> bool:
    if FoodModel.get_by_code(code):
        return True
    try:
        return FoodModel.lookup_code(code) is not None
    except Exception:  # noqa: BLE001 — OFF down: the local check above is all we can do
        return False


def _own_custom_food(food_id: str) -> dict:
    """Only the owner edits a custom food; OFF foods are corrected via "Fix on Open Food Facts"."""
    food = FoodModel.get(food_id)
    if not food or food['source'] != 'custom' or food['userID'] != session['user_id']:
        abort(404)
    return food


def _editable_food(food_id: str) -> dict:
    """OFF foods are shared; custom foods only by their owner."""
    food = FoodModel.get(food_id)
    if not food or (food['source'] == 'custom' and food['userID'] != session['user_id']):
        abort(404)
    return food
