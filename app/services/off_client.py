"""
Thin client for Open Food Facts (https://openfoodfacts.github.io/openfoodfacts-server/api/).

Reads always hit production OFF. Writes go to OFF_WRITE_URL (staging in dev, so testing
contributions never pollutes the real database) with the site-wide OFF_USER / OFF_PASSWORD.
"""
import requests
from flask import current_app

USER_AGENT = 'JTTBH/1.0 (https://jttbh.com)'
READ_URL = 'https://world.openfoodfacts.org'
SEARCH_URL = 'https://search.openfoodfacts.org/search'
FIELDS = 'code,product_name,brands,serving_quantity,nutriments'

# our column -> OFF nutriment key (all per 100 g; sodium in grams)
NUTRIENTS = {
    'kcal': 'energy-kcal', 'protein': 'proteins', 'carbs': 'carbohydrates', 'fat': 'fat',
    'fiber': 'fiber', 'sugar': 'sugars', 'sodium': 'sodium',
}

_GRAMS_PER = {'g': 1, 'kg': 1000, 'oz': 28.3495, 'lb': 453.592}


def product_to_food(p: dict) -> dict:
    """Map an OFF product (v2 API or search hit) to `food` column values."""
    n = p.get('nutriments') or {}
    brands = p.get('brands')
    if isinstance(brands, list):
        brands = ', '.join(brands)
    food = {
        'code': str(p.get('code') or '') or None,
        'name': (p.get('product_name') or '').strip() or f"Product {p.get('code')}",
        'brand': brands or None,
        'serving_g': _num(p.get('serving_quantity')),
    }
    for col, key in NUTRIENTS.items():
        food[col] = _num(n.get(f'{key}_100g'))
    return food


def lookup(code: str) -> dict | None:
    """Fetch one product by barcode. None if OFF doesn't know it."""
    r = requests.get(f'{READ_URL}/api/v2/product/{code}', params={'fields': FIELDS},
                     headers={'User-Agent': USER_AGENT}, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get('status') != 1:
        return None
    return product_to_food(data['product'])


def search(q: str, page_size: int = 15) -> list[dict]:
    r = requests.get(SEARCH_URL, params={'q': q, 'page_size': page_size, 'fields': FIELDS},
                     headers={'User-Agent': USER_AGENT}, timeout=10)
    r.raise_for_status()
    return [product_to_food(h) for h in r.json().get('hits', []) if h.get('code')]


def contribute(food: dict) -> None:
    """Create/update a product on OFF from `food` column values. Raises on failure."""
    cfg = current_app.config
    if not cfg.get('OFF_USER') or not cfg.get('OFF_PASSWORD'):
        raise RuntimeError('OFF_USER / OFF_PASSWORD are not set in .env.')
    form = {
        'code': food['code'],
        'user_id': cfg['OFF_USER'],
        'password': cfg['OFF_PASSWORD'],
        'product_name': food['name'],
        'nutrition_data_per': '100g',
        'comment': 'Added via JTTBH',
    }
    if food.get('brand'):
        form['brands'] = food['brand']
    if food.get('serving_g'):
        form['serving_size'] = f"{food['serving_g']} g"
    for col, key in NUTRIENTS.items():
        if food.get(col) is not None:
            form[f'nutriment_{key}'] = food[col]
            form[f'nutriment_{key}_unit'] = 'kcal' if col == 'kcal' else 'g'
    base = cfg.get('OFF_WRITE_URL') or READ_URL
    # staging (.net) sits behind HTTP basic auth off:off
    auth = ('off', 'off') if base.endswith('.net') else None
    r = requests.post(f'{base}/cgi/product_jqm2.pl', data=form, auth=auth,
                      headers={'User-Agent': USER_AGENT}, timeout=20)
    r.raise_for_status()
    result = r.json()
    if result.get('status') != 1:
        raise RuntimeError(result.get('status_verbose') or 'Open Food Facts rejected the product.')


def to_grams(amount, unit: str, serving_g=None) -> float | None:
    """Convert a recipe amount to grams. None when it needs a human (cups, cloves…)."""
    amt = _num(amount)
    if amt is None:
        return None
    unit = (unit or '').strip().lower()
    if unit in _GRAMS_PER:
        return round(amt * _GRAMS_PER[unit], 1)
    if unit in ('', 'serving', 'servings') and serving_g:
        return round(amt * float(serving_g), 1)
    return None


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
