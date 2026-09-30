# TODO

## Meal / macro tracker (Open Food Facts) — built 2026-09-30, not committed

- [x] Migration `migrations/20261001_meal.sql` (food, meal, meal_item, perm row) — applied to dev DB; **PROD still needs it**
- [x] `app/services/off_client.py` (lookup, search, contribute, to_grams)
- [x] `app/models/meal_model.py` (FoodModel, MealModel, recipe_nutrition)
- [x] Recipe links: `foodID`/`grams` in ingredients JSON; nutrition + link pages; detail per-serving line
- [x] `/<username>/meal/…` routes + templates + meal.css; nav + PERM_MEAL 131072
- [x] API: food/<barcode>, meals GET/POST, meals/<id>/items
- [x] test/test_meal.py (8 passing); browser + curl flow verified on dev
- [ ] Set `OFF_USER` / `OFF_PASSWORD` in .env (dev writes go to staging world.openfoodfacts.net) and try one real contribution
- [ ] Run migration on prod

- [x] Edit item amount (scales snapshot), edit own custom foods (`/meal/food/mine`) — 2026-09-30
- [x] API: all GETs now check the key's read bit (`_require_read`); test/test_api_perms.py

### Skipped for now
- Daily macro targets, charts, volume→grams density table
