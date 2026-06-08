import json
import uuid

from app.services.database import db_manager

_CURRENT_RECIPE_SQL = """
    SELECT r.recipeID, r.title, r.type, r.servings, r.prep_time, r.cook_time,
           r.source, r.ingredients, r.directions, r.notes,
           r.favorite, r.want_to_try, r.position, r.created
    FROM recipe r
    WHERE r.userID = %s
      AND r.id = (SELECT MAX(r2.id) FROM recipe r2 WHERE r2.recipeID = r.recipeID)
      AND r.title IS NOT NULL
"""


class RecipeModel:

    @staticmethod
    def get_recipes(user_id: str) -> list[dict]:
        return db_manager.execute_query(
            _CURRENT_RECIPE_SQL + " ORDER BY r.type, r.position, r.created",
            (user_id,),
        )

    @staticmethod
    def get_recipe(recipe_id: str, user_id: str) -> dict | None:
        recipe = db_manager.execute_one(
            _CURRENT_RECIPE_SQL + " AND r.recipeID = %s",
            (user_id, recipe_id),
        )
        if not recipe:
            return None
        recipe['ingredients_list'] = json.loads(recipe['ingredients']) if recipe.get('ingredients') else []
        recipe['directions_list'] = json.loads(recipe['directions']) if recipe.get('directions') else []
        return recipe

    @staticmethod
    def create_recipe(user_id: str, data: dict) -> str:
        recipe_id = str(uuid.uuid4())
        _insert_recipe_row(recipe_id, user_id, data)
        return recipe_id

    @staticmethod
    def update_recipe(recipe_id: str, user_id: str, data: dict) -> None:
        _insert_recipe_row(recipe_id, user_id, data)

    @staticmethod
    def delete_recipe(recipe_id: str, user_id: str) -> None:
        db_manager.execute_insert(
            """INSERT INTO recipe (recipeID, userID, title, created)
               VALUES (%s, %s, NULL, NOW())""",
            (recipe_id, user_id),
        )

    @staticmethod
    def toggle_favorite(recipe_id: str, user_id: str) -> bool | None:
        row = db_manager.execute_one(
            """SELECT id, favorite FROM recipe
               WHERE recipeID = %s AND userID = %s AND title IS NOT NULL
               ORDER BY id DESC LIMIT 1""",
            (recipe_id, user_id),
        )
        if not row:
            return None
        new_val = 0 if row['favorite'] else 1
        db_manager.execute_insert(
            """INSERT INTO recipe
                 (recipeID, userID, title, source, type, servings, prep_time, cook_time,
                  ingredients, directions, notes, position, favorite, want_to_try, created, created_by)
               SELECT
                 recipeID, userID, title, source, type, servings, prep_time, cook_time,
                 ingredients, directions, notes, position, %s, want_to_try, NOW(), created_by
               FROM recipe WHERE id = %s""",
            (new_val, row['id']),
        )
        return bool(new_val)

    @staticmethod
    def toggle_want_to_try(recipe_id: str, user_id: str) -> bool | None:
        row = db_manager.execute_one(
            """SELECT id, want_to_try FROM recipe
               WHERE recipeID = %s AND userID = %s AND title IS NOT NULL
               ORDER BY id DESC LIMIT 1""",
            (recipe_id, user_id),
        )
        if not row:
            return None
        new_val = 0 if row['want_to_try'] else 1
        db_manager.execute_insert(
            """INSERT INTO recipe
                 (recipeID, userID, title, source, type, servings, prep_time, cook_time,
                  ingredients, directions, notes, position, favorite, want_to_try, created, created_by)
               SELECT
                 recipeID, userID, title, source, type, servings, prep_time, cook_time,
                 ingredients, directions, notes, position, favorite, %s, NOW(), created_by
               FROM recipe WHERE id = %s""",
            (new_val, row['id']),
        )
        return bool(new_val)

    @staticmethod
    def search_recipes(user_id: str, query: str) -> list[dict]:
        q = f'%{query}%'
        return db_manager.execute_query(
            _CURRENT_RECIPE_SQL + """
              AND (r.title LIKE %s
                   OR r.notes LIKE %s
                   OR r.source LIKE %s
                   OR r.ingredients LIKE %s)
              ORDER BY r.type, r.title
            """,
            (user_id, q, q, q, q),
        )

    @staticmethod
    def get_images(recipe_id: str, user_id: str) -> list[dict]:
        return db_manager.execute_query(
            "SELECT imageID, url, caption, position FROM recipe_image WHERE recipeID = %s AND userID = %s ORDER BY position, id",
            (recipe_id, user_id),
        )

    @staticmethod
    def add_image(recipe_id: str, user_id: str, url: str, caption: str = '') -> str:
        image_id = str(uuid.uuid4())
        max_pos = db_manager.execute_one(
            "SELECT COALESCE(MAX(position), 0) AS m FROM recipe_image WHERE recipeID = %s AND userID = %s",
            (recipe_id, user_id),
        )
        position = (max_pos['m'] if max_pos else 0) + 1
        db_manager.execute_insert(
            "INSERT INTO recipe_image (imageID, recipeID, userID, url, caption, position, created) VALUES (%s,%s,%s,%s,%s,%s,NOW())",
            (image_id, recipe_id, user_id, url, caption or None, position),
        )
        return image_id

    @staticmethod
    def delete_image(image_id: str, user_id: str) -> dict | None:
        row = db_manager.execute_one(
            "SELECT imageID, url FROM recipe_image WHERE imageID = %s AND userID = %s",
            (image_id, user_id),
        )
        if row:
            db_manager.execute_update(
                "DELETE FROM recipe_image WHERE imageID = %s AND userID = %s",
                (image_id, user_id),
            )
        return row

    @staticmethod
    def source_exists(user_id: str, source_url: str) -> bool:
        row = db_manager.execute_one(
            _CURRENT_RECIPE_SQL + " AND r.source = %s",
            (user_id, source_url),
        )
        return row is not None


def _insert_recipe_row(recipe_id: str, user_id: str, data: dict) -> None:
    db_manager.execute_insert(
        """INSERT INTO recipe
           (recipeID, userID, title, source, type, servings, prep_time, cook_time,
            ingredients, directions, notes, position, favorite, want_to_try, created, created_by)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s)""",
        (
            recipe_id,
            user_id,
            data.get('title') or None,
            data.get('source') or None,
            data.get('type') or None,
            data.get('servings') or None,
            data.get('prep_time') or None,
            data.get('cook_time') or None,
            json.dumps(data.get('ingredients') or []),
            json.dumps(data.get('directions') or []),
            data.get('notes') or None,
            int(data.get('position') or 0),
            int(data.get('favorite') or 0),
            int(data.get('want_to_try') or 0),
            user_id,
        ),
    )
