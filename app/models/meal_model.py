import re
import uuid
from datetime import date, timedelta

from app.services import off_client
from app.services.database import db_manager

MACROS = ('kcal', 'protein', 'carbs', 'fat')
_FOOD_COLS = 'foodID, code, userID, name, brand, serving_g, kcal, protein, carbs, fat, fiber, sugar, sodium, source'

_CURRENT_MEAL_SQL = """
    SELECT m.mealID, m.name, m.eaten_at
    FROM meal m
    WHERE m.userID = %s
      AND m.id = (SELECT MAX(m2.id) FROM meal m2 WHERE m2.mealID = m.mealID)
      AND m.name IS NOT NULL
"""

_CURRENT_ITEM_SQL = """
    SELECT i.itemID, i.mealID, i.label, i.recipeID, i.foodID, i.quantity, i.unit,
           i.kcal, i.protein, i.carbs, i.fat
    FROM meal_item i
    WHERE i.userID = %s
      AND i.id = (SELECT MAX(i2.id) FROM meal_item i2 WHERE i2.itemID = i.itemID)
      AND i.label IS NOT NULL
"""


# ---------------------------------------------------------------------------
# Nutrition math (pure; tested in test/test_meal.py)
# ---------------------------------------------------------------------------

def food_macros(food: dict, grams: float) -> dict:
    """Macros for `grams` of a food whose nutrients are per 100 g."""
    return {k: round(float(food.get(k) or 0) * float(grams) / 100, 1) for k in MACROS}


def sum_macros(rows) -> dict:
    rows = list(rows)  # iterated once per macro; a generator would be empty after kcal
    return {k: round(sum(float(r.get(k) or 0) for r in rows), 1) for k in MACROS}


def parse_servings(servings) -> float:
    m = re.match(r'\s*(\d+(?:\.\d+)?)', str(servings or ''))
    return float(m.group(1)) if m and float(m.group(1)) > 0 else 1.0


def recipe_nutrition(recipe: dict, foods: dict) -> dict:
    """
    Nutrition for a recipe from its linked ingredients.
    `foods` maps foodID -> food row. Ingredients missing a food or grams are 'unlinked'
    and contribute nothing, so the caller can warn that totals are incomplete.
    """
    parts, unlinked = [], []
    for ing in recipe.get('ingredients_list') or []:
        if ing.get('subtitle'):
            continue
        food = foods.get(ing.get('foodID'))
        if food and ing.get('grams'):
            parts.append(food_macros(food, ing['grams']))
        else:
            unlinked.append(ing.get('item'))
    total = sum_macros(parts)
    servings = parse_servings(recipe.get('servings'))
    return {
        'total': total,
        'servings': servings,
        'per_serving': {k: round(v / servings, 1) for k, v in total.items()},
        'unlinked': unlinked,
    }


# ---------------------------------------------------------------------------
# Food (local cache of Open Food Facts + custom foods)
# ---------------------------------------------------------------------------

class FoodModel:

    @staticmethod
    def get(food_id: str) -> dict | None:
        return db_manager.execute_one(f'SELECT {_FOOD_COLS} FROM food WHERE foodID = %s', (food_id,))

    @staticmethod
    def get_many(food_ids) -> dict:
        ids = [f for f in set(food_ids) if f]
        if not ids:
            return {}
        rows = db_manager.execute_query(
            f"SELECT {_FOOD_COLS} FROM food WHERE foodID IN ({','.join(['%s'] * len(ids))})",
            tuple(ids),
        )
        return {r['foodID']: r for r in rows}

    @staticmethod
    def upsert_off(food: dict) -> str:
        """Insert or refresh an OFF product in the cache; return its foodID."""
        vals = [food.get(c) for c in ('name', 'brand', 'serving_g') + tuple(off_client.NUTRIENTS)]
        db_manager.execute_insert(
            """INSERT INTO food (foodID, code, name, brand, serving_g, kcal, protein, carbs, fat,
                                 fiber, sugar, sodium, source, fetched)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'off',NOW())
               ON DUPLICATE KEY UPDATE name=VALUES(name), brand=VALUES(brand),
                 serving_g=VALUES(serving_g), kcal=VALUES(kcal), protein=VALUES(protein),
                 carbs=VALUES(carbs), fat=VALUES(fat), fiber=VALUES(fiber), sugar=VALUES(sugar),
                 sodium=VALUES(sodium), source='off', userID=NULL, fetched=NOW()""",
            (str(uuid.uuid4()), food['code'], *vals),
        )
        return db_manager.execute_one('SELECT foodID FROM food WHERE code = %s', (food['code'],))['foodID']

    @staticmethod
    def lookup_code(code: str, refresh: bool = False) -> dict | None:
        """Cached food for a barcode, fetching from OFF on a miss. None if unknown everywhere."""
        if not refresh:
            row = FoodModel.get_by_code(code)
            if row:
                return row
        food = off_client.lookup(code)
        if not food:
            return None
        return FoodModel.get(FoodModel.upsert_off(food))

    @staticmethod
    def search(user_id: str, q: str) -> tuple[list[dict], str | None]:
        """Local matches first, then OFF hits (cached as they arrive). Returns (foods, off_error)."""
        if re.fullmatch(r'\d{8,14}', q):
            try:
                food = FoodModel.lookup_code(q)
            except Exception as e:  # noqa: BLE001
                return [], str(e)
            return ([food] if food else []), None
        like = f'%{q}%'
        local = list(db_manager.execute_query(
            f"""SELECT {_FOOD_COLS} FROM food
                WHERE (source = 'off' OR userID = %s) AND (name LIKE %s OR brand LIKE %s OR code = %s)
                ORDER BY source = 'custom' DESC, name LIMIT 20""",
            (user_id, like, like, q),
        ))
        error = None
        try:
            remote_ids = [FoodModel.upsert_off(f) for f in off_client.search(q)]
        except Exception as e:  # noqa: BLE001 — OFF being down must not break local search
            remote_ids, error = [], str(e)
        seen = {f['foodID'] for f in local}
        remote = FoodModel.get_many(remote_ids)
        return local + [remote[i] for i in remote_ids if i in remote and i not in seen], error

    @staticmethod
    def get_by_code(code: str) -> dict | None:
        return db_manager.execute_one(f'SELECT {_FOOD_COLS} FROM food WHERE code = %s', (code,))

    @staticmethod
    def update(food_id: str, food: dict) -> None:
        """Direct UPDATE (food is a cache table): mirror what was just sent to OFF."""
        cols = ('code', 'name', 'brand', 'serving_g') + tuple(off_client.NUTRIENTS)
        db_manager.execute_update(
            f"UPDATE food SET {', '.join(f'{c} = %s' for c in cols)} WHERE foodID = %s",
            (*[food.get(c) for c in cols], food_id),
        )

    @staticmethod
    def get_custom(user_id: str) -> list[dict]:
        return list(db_manager.execute_query(
            f"SELECT {_FOOD_COLS} FROM food WHERE source = 'custom' AND userID = %s ORDER BY name", (user_id,),
        ))

    @staticmethod
    def create_custom(user_id: str, food: dict) -> str:
        food_id = str(uuid.uuid4())
        db_manager.execute_insert(
            """INSERT INTO food (foodID, code, userID, name, brand, serving_g, kcal, protein, carbs, fat,
                                 fiber, sugar, sodium, source)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'custom')""",
            (food_id, food.get('code') or None, user_id, food['name'], food.get('brand') or None,
             *[food.get(c) for c in ('serving_g',) + tuple(off_client.NUTRIENTS)]),
        )
        return food_id


# ---------------------------------------------------------------------------
# Meals
# ---------------------------------------------------------------------------

class MealModel:

    @staticmethod
    def get_day(user_id: str, day: date) -> list[dict]:
        meals = db_manager.execute_query(
            _CURRENT_MEAL_SQL + ' AND m.eaten_at >= %s AND m.eaten_at < %s ORDER BY m.eaten_at',
            (user_id, day, day + timedelta(days=1)),
        )
        if not meals:
            return []
        ids = [m['mealID'] for m in meals]
        items = db_manager.execute_query(
            _CURRENT_ITEM_SQL + f" AND i.mealID IN ({','.join(['%s'] * len(ids))}) ORDER BY i.id",
            (user_id, *ids),
        )
        for m in meals:
            m['items'] = [i for i in items if i['mealID'] == m['mealID']]
            m['totals'] = sum_macros(m['items'])
        return meals

    @staticmethod
    def get_meal(meal_id: str, user_id: str) -> dict | None:
        return db_manager.execute_one(_CURRENT_MEAL_SQL + ' AND m.mealID = %s', (user_id, meal_id))

    @staticmethod
    def save_meal(user_id: str, name: str, eaten_at, meal_id: str | None = None) -> str:
        """Create (meal_id None) or update a meal. Insert-only either way."""
        meal_id = meal_id or str(uuid.uuid4())
        db_manager.execute_insert(
            'INSERT INTO meal (mealID, userID, name, eaten_at) VALUES (%s,%s,%s,%s)',
            (meal_id, user_id, name, eaten_at),
        )
        return meal_id

    @staticmethod
    def delete_meal(meal_id: str, user_id: str, eaten_at) -> None:
        db_manager.execute_insert(
            'INSERT INTO meal (mealID, userID, name, eaten_at) VALUES (%s,%s,NULL,%s)',
            (meal_id, user_id, eaten_at),
        )

    @staticmethod
    def add_item(user_id: str, meal_id: str, label: str, quantity: float, unit: str,
                 macros: dict, recipe_id: str | None = None, food_id: str | None = None) -> str:
        item_id = str(uuid.uuid4())
        db_manager.execute_insert(
            """INSERT INTO meal_item (itemID, mealID, userID, label, recipeID, foodID, quantity, unit,
                                      kcal, protein, carbs, fat)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (item_id, meal_id, user_id, label, recipe_id, food_id, quantity, unit,
             *[macros[k] for k in MACROS]),
        )
        return item_id

    @staticmethod
    def update_item(item_id: str, user_id: str, quantity: float) -> str | None:
        """
        Change an item's amount; returns its mealID (None if not found/not owned).
        Macros scale from the logged snapshot, not the current recipe/food, so history stays put.
        """
        item = db_manager.execute_one(_CURRENT_ITEM_SQL + ' AND i.itemID = %s', (user_id, item_id))
        if not item:
            return None
        ratio = quantity / float(item['quantity'])
        db_manager.execute_insert(
            """INSERT INTO meal_item (itemID, mealID, userID, label, recipeID, foodID, quantity, unit,
                                      kcal, protein, carbs, fat)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (item_id, item['mealID'], user_id, item['label'], item['recipeID'], item['foodID'], quantity,
             item['unit'], *[round(float(item[k] or 0) * ratio, 1) for k in MACROS]),
        )
        return item['mealID']

    @staticmethod
    def delete_item(item_id: str, user_id: str) -> str | None:
        """Soft-delete an item; returns its mealID (None if not found/not owned)."""
        item = db_manager.execute_one(_CURRENT_ITEM_SQL + ' AND i.itemID = %s', (user_id, item_id))
        if not item:
            return None
        db_manager.execute_insert(
            """INSERT INTO meal_item (itemID, mealID, userID, label, quantity, unit)
               VALUES (%s,%s,%s,NULL,%s,%s)""",
            (item_id, item['mealID'], user_id, item['quantity'], item['unit']),
        )
        return item['mealID']

    @staticmethod
    def add_recipe(user_id: str, meal_id: str, recipe: dict, servings: float) -> tuple[str, list]:
        """Log `servings` of a recipe (from RecipeModel.get_recipe). Returns (itemID, unlinked ingredient names)."""
        foods = FoodModel.get_many(i.get('foodID') for i in recipe['ingredients_list'])
        n = recipe_nutrition(recipe, foods)
        macros = {k: round(v * servings, 1) for k, v in n['per_serving'].items()}
        item_id = MealModel.add_item(user_id, meal_id, recipe['title'], servings, 'serving', macros,
                                     recipe_id=recipe['recipeID'])
        return item_id, n['unlinked']

    @staticmethod
    def add_food(user_id: str, meal_id: str, food: dict, grams: float) -> str:
        label = food['name'] + (f" ({food['brand']})" if food.get('brand') else '')
        return MealModel.add_item(user_id, meal_id, label, grams, 'g', food_macros(food, grams),
                                  food_id=food['foodID'])
