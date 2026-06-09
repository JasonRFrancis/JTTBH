import io
import json
import os
import re
import uuid

import requests
from bs4 import BeautifulSoup
from flask import (
    Blueprint, abort, current_app, flash, jsonify, redirect,
    render_template, request, send_file, session, url_for,
)

from app.models.recipe_model import RecipeModel
from app.services.decorators import (
    PERM_RECIPE,
    login_required,
    permission_required_read,
    permission_required_write,
)

recipe_bp = Blueprint('recipe', __name__)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
_STOP_WORDS = frozenset({'a', 'an', 'the'})


def _sort_key(title: str) -> str:
    words = (title or '').strip().split()
    if words and words[0].lower() in _STOP_WORDS:
        words = words[1:]
    return ' '.join(words).lower()


# ---------------------------------------------------------------------------
# GET routes
# ---------------------------------------------------------------------------

@recipe_bp.route('/index')
@login_required
@permission_required_read(PERM_RECIPE)
def index(username: str):
    recipes = RecipeModel.get_recipes(session['user_id'])
    groups: dict[str, list] = {}
    for r in recipes:
        key = (r['type'] or 'Uncategorized').strip()
        groups.setdefault(key, []).append(r)
    sorted_groups = []
    for type_name in sorted(groups.keys(), key=lambda x: (x == 'Uncategorized', x.lower())):
        group = groups[type_name]
        favorites = sorted([r for r in group if r.get('favorite')], key=lambda r: _sort_key(r['title']))
        rest = sorted([r for r in group if not r.get('favorite')], key=lambda r: _sort_key(r['title']))
        sorted_groups.append((type_name, favorites, rest))
    return render_template('recipe_index.html', username=username, area='recipe', groups=sorted_groups)


@recipe_bp.route('/archive')
@login_required
@permission_required_read(PERM_RECIPE)
def archive_view(username: str):
    recipes = RecipeModel.get_archived_recipes(session['user_id'])
    return render_template('recipe_archive.html', username=username, area='recipe', recipes=recipes)


@recipe_bp.route('/search')
@login_required
@permission_required_read(PERM_RECIPE)
def search(username: str):
    q = request.args.get('q', '').strip()
    results = RecipeModel.search_recipes(session['user_id'], q) if q else []
    return render_template('recipe_search.html', username=username, area='recipe', q=q, results=results)


@recipe_bp.route('/detail/<recipe_id>')
@login_required
@permission_required_read(PERM_RECIPE)
def detail(username: str, recipe_id: str):
    recipe = RecipeModel.get_recipe(recipe_id, session['user_id'])
    if not recipe:
        abort(404)
    images = RecipeModel.get_images(recipe_id, session['user_id'])
    return render_template('recipe_detail.html', username=username, area='recipe', recipe=recipe, images=images)


@recipe_bp.route('/add')
@login_required
@permission_required_read(PERM_RECIPE)
def add(username: str):
    return render_template('recipe_form.html', username=username, area='recipe', recipe=None, images=[])


@recipe_bp.route('/edit/<recipe_id>')
@login_required
@permission_required_read(PERM_RECIPE)
def edit(username: str, recipe_id: str):
    recipe = RecipeModel.get_recipe(recipe_id, session['user_id'])
    if not recipe:
        abort(404)
    images = RecipeModel.get_images(recipe_id, session['user_id'])
    return render_template('recipe_form.html', username=username, area='recipe', recipe=recipe, images=images)


# ---------------------------------------------------------------------------
# POST — extract
# ---------------------------------------------------------------------------

@recipe_bp.route('/extract/post', methods=['POST'])
@login_required
@permission_required_read(PERM_RECIPE)
def extract(username: str):
    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()
    if not url:
        return jsonify({'status': 'error', 'message': 'No URL provided.'})
    try:
        result = _extract_recipe(url)
        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:  # noqa: BLE001
        return jsonify({'status': 'error', 'message': str(e)})


# ---------------------------------------------------------------------------
# POST — CRUD
# ---------------------------------------------------------------------------

@recipe_bp.route('/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_RECIPE)
@permission_required_write(PERM_RECIPE)
def create(username: str):
    data = _form_to_recipe_data()
    if not data.get('title'):
        flash('Title is required.', 'error')
        return redirect(url_for('recipe.add', username=username))
    recipe_id = RecipeModel.create_recipe(session['user_id'], data)
    flash('Recipe created.', 'success')
    return redirect(url_for('recipe.detail', username=username, recipe_id=recipe_id))


@recipe_bp.route('/update/post/<recipe_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_RECIPE)
@permission_required_write(PERM_RECIPE)
def update(username: str, recipe_id: str):
    recipe = RecipeModel.get_recipe(recipe_id, session['user_id'])
    if not recipe:
        abort(404)
    data = _form_to_recipe_data()
    if not data.get('title'):
        flash('Title is required.', 'error')
        return redirect(url_for('recipe.edit', username=username, recipe_id=recipe_id))
    data['favorite'] = recipe.get('favorite', 0)
    data['want_to_try'] = recipe.get('want_to_try', 0)
    data['archived'] = recipe.get('archived', 0)
    RecipeModel.update_recipe(recipe_id, session['user_id'], data)
    flash('Recipe updated.', 'success')
    return redirect(url_for('recipe.detail', username=username, recipe_id=recipe_id))


@recipe_bp.route('/delete/post/<recipe_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_RECIPE)
@permission_required_write(PERM_RECIPE)
def delete(username: str, recipe_id: str):
    recipe = RecipeModel.get_recipe(recipe_id, session['user_id'])
    if not recipe:
        abort(404)
    RecipeModel.delete_recipe(recipe_id, session['user_id'])
    flash('Recipe deleted.', 'success')
    return redirect(url_for('recipe.index', username=username))


@recipe_bp.route('/favorite/toggle/post/<recipe_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_RECIPE)
@permission_required_write(PERM_RECIPE)
def favorite_toggle(username: str, recipe_id: str):
    new_val = RecipeModel.toggle_favorite(recipe_id, session['user_id'])
    if new_val is None:
        return jsonify({'status': 'error', 'message': 'Recipe not found.'})
    return jsonify({'status': 'ok', 'favorite': new_val})


@recipe_bp.route('/want_to_try/toggle/post/<recipe_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_RECIPE)
@permission_required_write(PERM_RECIPE)
def want_to_try_toggle(username: str, recipe_id: str):
    new_val = RecipeModel.toggle_want_to_try(recipe_id, session['user_id'])
    if new_val is None:
        return jsonify({'status': 'error', 'message': 'Recipe not found.'})
    return jsonify({'status': 'ok', 'want_to_try': new_val})


@recipe_bp.route('/archive/toggle/post/<recipe_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_RECIPE)
@permission_required_write(PERM_RECIPE)
def archive_toggle(username: str, recipe_id: str):
    new_val = RecipeModel.toggle_archive(recipe_id, session['user_id'])
    if new_val is None:
        return jsonify({'status': 'error', 'message': 'Recipe not found.'})
    return jsonify({'status': 'ok', 'archived': new_val})


# ---------------------------------------------------------------------------
# POST — images
# ---------------------------------------------------------------------------

@recipe_bp.route('/image/add/post/<recipe_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_RECIPE)
@permission_required_write(PERM_RECIPE)
def image_add(username: str, recipe_id: str):
    recipe = RecipeModel.get_recipe(recipe_id, session['user_id'])
    if not recipe:
        return jsonify({'status': 'error', 'message': 'Recipe not found.'})

    caption = request.form.get('caption', '').strip()
    file = request.files.get('image_file')
    url = request.form.get('image_url', '').strip()

    if file and file.filename:
        ext = file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({'status': 'error', 'message': 'File type not allowed.'})
        filename = f"{uuid.uuid4()}.{ext}"
        upload_dir = current_app.config.get('UPLOAD_FOLDER', '')
        if not upload_dir:
            return jsonify({'status': 'error', 'message': 'Upload folder not configured.'})
        os.makedirs(upload_dir, exist_ok=True)
        file.save(os.path.join(upload_dir, filename))
        url = f"/static/uploads/recipes/{filename}"
    elif not url:
        return jsonify({'status': 'error', 'message': 'No image provided.'})

    image_id = RecipeModel.add_image(recipe_id, session['user_id'], url, caption)
    return jsonify({'status': 'ok', 'imageID': image_id, 'url': url, 'caption': caption})


@recipe_bp.route('/image/delete/post/<image_id>', methods=['POST'])
@login_required
@permission_required_read(PERM_RECIPE)
@permission_required_write(PERM_RECIPE)
def image_delete(username: str, image_id: str):
    row = RecipeModel.delete_image(image_id, session['user_id'])
    if not row:
        return jsonify({'status': 'error', 'message': 'Image not found.'})
    # Delete local file if it was uploaded
    img_url = row.get('url', '')
    if img_url.startswith('/static/uploads/recipes/'):
        filename = img_url.rsplit('/', 1)[-1]
        upload_dir = current_app.config.get('UPLOAD_FOLDER', '')
        if upload_dir:
            filepath = os.path.join(upload_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
    return jsonify({'status': 'ok'})


# ---------------------------------------------------------------------------
# POST — PDF export
# ---------------------------------------------------------------------------

@recipe_bp.route('/pdf/post', methods=['POST'])
@login_required
@permission_required_read(PERM_RECIPE)
def pdf(username: str):
    recipe_ids = request.form.getlist('recipe_id')
    if not recipe_ids:
        flash('Select at least one recipe.', 'error')
        return redirect(url_for('recipe.index', username=username))

    user_id = session['user_id']
    recipes = []
    for rid in recipe_ids:
        r = RecipeModel.get_recipe(rid, user_id)
        if r:
            r['images'] = RecipeModel.get_images(rid, user_id)
            recipes.append(r)

    if not recipes:
        flash('No valid recipes selected.', 'error')
        return redirect(url_for('recipe.index', username=username))

    html = render_template('recipe_pdf.html', recipes=recipes)

    try:
        import weasyprint
        pdf_bytes = weasyprint.HTML(string=html, base_url=request.url_root).write_pdf()
    except Exception as e:  # noqa: BLE001
        flash(f'PDF generation failed: {e}', 'error')
        return redirect(url_for('recipe.index', username=username))

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='recipes.pdf',
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _form_to_recipe_data() -> dict:
    from app.services.recipe_utils import parse_amount_input, standardize_unit  # noqa: PLC0415
    amounts = request.form.getlist('ingredient_amount[]')
    units = request.form.getlist('ingredient_unit[]')
    items = request.form.getlist('ingredient_item[]')
    notes_list = request.form.getlist('ingredient_note[]')
    is_subtitles = request.form.getlist('ingredient_is_subtitle[]')
    # Pad is_subtitles to match items length for forms that predate this field
    while len(is_subtitles) < len(items):
        is_subtitles.append('')
    ingredients = []
    for a, u, i, n, sub in zip(amounts, units, items, notes_list, is_subtitles):
        if sub:
            if i.strip():
                ingredients.append({'subtitle': i.strip()})
        elif i.strip():
            ingredients.append({
                'amount': parse_amount_input(a),
                'unit': standardize_unit(u.strip()),
                'item': i.strip(),
                'note': n.strip(),
            })
    directions = [d.strip() for d in request.form.getlist('direction[]') if d.strip()]
    return {
        'title': request.form.get('title', '').strip(),
        'source': request.form.get('source', '').strip(),
        'type': request.form.get('type', '').strip(),
        'servings': request.form.get('servings', '').strip(),
        'prep_time': request.form.get('prep_time', '').strip(),
        'cook_time': request.form.get('cook_time', '').strip(),
        'ingredients': ingredients,
        'directions': directions,
        'notes': request.form.get('notes', '').strip(),
    }


def _extract_recipe(url: str) -> dict:
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
    r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')

    for script in soup.find_all('script', {'type': 'application/ld+json'}):
        try:
            raw = json.loads(script.string or '')
        except (json.JSONDecodeError, AttributeError):
            continue
        # Unwrap @graph arrays
        if isinstance(raw, dict) and '@graph' in raw:
            raw = raw['@graph']
        candidates = raw if isinstance(raw, list) else [raw]
        for node in candidates:
            if isinstance(node, dict) and node.get('@type') == 'Recipe':
                return _parse_jsonld(node)

    # Fallback: Open Graph title + image only
    result = {}
    og = soup.find('meta', {'property': 'og:title'})
    if og:
        result['title'] = og.get('content', '').strip()
    og_img = soup.find('meta', {'property': 'og:image'})
    if og_img:
        result['images'] = [og_img.get('content', '').strip()]
    return result


def _parse_jsonld(data: dict) -> dict:
    result = {'title': (data.get('name') or '').strip()}

    yield_val = data.get('recipeYield')
    if yield_val:
        if isinstance(yield_val, list):
            yield_val = yield_val[0] if yield_val else ''
        result['servings'] = str(yield_val).strip()

    if data.get('prepTime'):
        result['prep_time'] = _iso_duration(data['prepTime'])
    if data.get('cookTime'):
        result['cook_time'] = _iso_duration(data['cookTime'])

    raw_ing = data.get('recipeIngredient')
    if raw_ing:
        from app.services.recipe_utils import parse_ingredient_text  # noqa: PLC0415
        parsed = [parse_ingredient_text(str(i)) for i in raw_ing if str(i).strip()]
        result['ingredients'] = [p for p in parsed if p]

    raw_instr = data.get('recipeInstructions')
    if raw_instr:
        directions = []
        if isinstance(raw_instr, str):
            directions = [raw_instr.strip()]
        elif isinstance(raw_instr, list):
            for step in raw_instr:
                if isinstance(step, str):
                    directions.append(step.strip())
                elif isinstance(step, dict):
                    directions.append((step.get('text') or '').strip())
        result['directions'] = [d for d in directions if d]

    raw_img = data.get('image')
    if raw_img:
        if isinstance(raw_img, str):
            imgs = [raw_img]
        elif isinstance(raw_img, list):
            imgs = [i if isinstance(i, str) else (i.get('url') or '') for i in raw_img]
        elif isinstance(raw_img, dict):
            imgs = [raw_img.get('url') or '']
        else:
            imgs = []
        result['images'] = [i.strip() for i in imgs if i and i.strip()]

    cat = data.get('recipeCategory')
    if cat:
        if isinstance(cat, list):
            cat = cat[0] if cat else ''
        result['type'] = str(cat).strip()

    return result


def _iso_duration(s: str) -> str:
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', str(s))
    if not m:
        return str(s)
    h, mins = m.group(1), m.group(2)
    parts = []
    if h:
        parts.append(f'{h}h')
    if mins:
        parts.append(f'{mins}m')
    return ' '.join(parts) or str(s)
