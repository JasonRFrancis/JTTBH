"""
Unit tests: meal tracker nutrition math
=======================================
Why this matters:

* A recipe logged as dinner must carry the macros of its *linked* ingredients,
  scaled to grams, divided by the recipe's servings, times servings eaten.
* Unlinked ingredients must be reported, not silently counted as zero, so the
  user knows the day's total is low.
* Weight units convert automatically; cups/cloves must return None so the UI
  asks for grams instead of guessing.
* Logged items are snapshots: the numbers written to meal_item are computed at
  log time, so editing the recipe later can't rewrite history.

DB access is mocked; no live database.

Run: pytest test/test_meal.py -v
"""

from unittest.mock import MagicMock

import pytest

from app.models import meal_model
from app.models.meal_model import MealModel, parse_servings, recipe_nutrition
from app.services.off_client import product_to_food, to_grams

BEEF = {'foodID': 'beef', 'name': 'Flank steak', 'kcal': 200, 'protein': 30, 'carbs': 0, 'fat': 8}
SOY = {'foodID': 'soy', 'name': 'Soy sauce', 'kcal': 60, 'protein': 8, 'carbs': 6, 'fat': 0}

RECIPE = {
    'recipeID': 'r1',
    'title': 'Crock Pot Mongolian Beef',
    'servings': '4 servings',
    'ingredients_list': [
        {'subtitle': 'Main'},
        {'amount': '2', 'unit': 'lb', 'item': 'flank steak', 'foodID': 'beef', 'grams': 907.2},
        {'amount': '0.5', 'unit': 'cup', 'item': 'soy sauce', 'foodID': 'soy', 'grams': 120},
        {'amount': '3', 'unit': 'clove', 'item': 'garlic'},
    ],
}


def test_to_grams_converts_weights_and_refuses_to_guess_volumes():
    assert to_grams('2', 'lb') == 907.2
    assert to_grams('8', 'oz') == 226.8
    assert to_grams('1.5', 'kg') == 1500
    assert to_grams('2', '', serving_g=30) == 60      # "2" of a packaged food = 2 servings
    assert to_grams('1', 'cup') is None
    assert to_grams('3', 'clove') is None
    assert to_grams('', 'g') is None


def test_parse_servings_defaults_to_one():
    assert parse_servings('4 servings') == 4
    assert parse_servings('Serves 6') == 1             # can't parse → whole recipe is one serving
    assert parse_servings(None) == 1
    assert parse_servings('0') == 1


def test_recipe_nutrition_sums_linked_and_reports_unlinked():
    n = recipe_nutrition(RECIPE, {'beef': BEEF, 'soy': SOY})
    # beef 907.2 g → 1814.4 kcal; soy 120 g → 72 kcal
    assert n['total']['kcal'] == pytest.approx(1886.4)
    assert n['per_serving']['kcal'] == pytest.approx(471.6)
    assert n['per_serving']['protein'] == pytest.approx((272.2 + 9.6) / 4, abs=0.1)
    assert n['unlinked'] == ['garlic']


def test_ingredient_linked_without_grams_counts_as_unlinked():
    recipe = {'servings': '1', 'ingredients_list': [{'item': 'steak', 'foodID': 'beef'}]}
    n = recipe_nutrition(recipe, {'beef': BEEF})
    assert n['total']['kcal'] == 0
    assert n['unlinked'] == ['steak']


def test_off_product_mapping_handles_list_brands_and_missing_nutrients():
    food = product_to_food({'code': '123', 'product_name': 'Soy Sauce', 'brands': ['A', 'B'],
                            'nutriments': {'energy-kcal_100g': 66.7, 'sodium_100g': 4.4}})
    assert food['brand'] == 'A, B'
    assert food['kcal'] == 66.7
    assert food['sodium'] == 4.4
    assert food['protein'] is None


@pytest.fixture
def db(monkeypatch):
    mock = MagicMock()
    mock.execute_query.return_value = [BEEF, SOY]
    monkeypatch.setattr(meal_model, 'db_manager', mock)
    return mock


def test_logged_recipe_is_a_snapshot_scaled_by_servings_eaten(db):
    _, unlinked = MealModel.add_recipe('u1', 'm1', RECIPE, servings=1.5)
    params = db.execute_insert.call_args[0][1]
    kcal, protein, carbs, fat = params[-4:]
    assert kcal == pytest.approx(471.6 * 1.5, abs=0.1)
    assert params[3] == 'Crock Pot Mongolian Beef'
    assert params[6:8] == (1.5, 'serving')
    assert unlinked == ['garlic']


def test_logged_food_scales_per_100g_by_grams(db):
    MealModel.add_food('u1', 'm1', SOY, grams=15)
    params = db.execute_insert.call_args[0][1]
    assert params[-4:] == (9.0, 1.2, 0.9, 0.0)


def test_sum_macros_accepts_a_generator():
    # The day total is built from a generator of per-meal totals; every macro must survive.
    totals = meal_model.sum_macros(m for m in [BEEF, SOY])
    assert totals == {'kcal': 260.0, 'protein': 38.0, 'carbs': 6.0, 'fat': 8.0}


def test_editing_amount_scales_the_logged_snapshot_not_the_current_recipe(db):
    # Logged 1 serving at 400 kcal; recipe may have changed since. Doubling must give 800, not a recompute.
    db.execute_one.return_value = {'itemID': 'i1', 'mealID': 'm1', 'label': 'Beef', 'recipeID': 'r1',
                                   'foodID': None, 'quantity': 1, 'unit': 'serving',
                                   'kcal': 400, 'protein': 30, 'carbs': 20, 'fat': 10}
    assert MealModel.update_item('i1', 'u1', 2) == 'm1'
    params = db.execute_insert.call_args[0][1]
    assert params[6:8] == (2, 'serving')
    assert params[-4:] == (800.0, 60.0, 40.0, 20.0)


def test_editing_someone_elses_item_does_nothing(db):
    db.execute_one.return_value = None
    assert MealModel.update_item('i1', 'intruder', 2) is None
    db.execute_insert.assert_not_called()
