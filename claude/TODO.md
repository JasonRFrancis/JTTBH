# TODO

## Journal templates — built 2026-10-06, not committed

Template markup (one question per line, type in trailing `[brackets]`, `# ` = heading, blank lines ignored):
`Question` → textarea · `[line]` text · `[number]` · `[check]` checkbox · `[a|b|c]` radio

- [x] Migration `migrations/20261006_journal_template.sql` — applied to dev DB; **PROD still needs it**
  - `journal_template` (id, userID, body TEXT, created) — insert-only, latest row = current template
  - `journal_entry` (id, entryID, userID, answered DATE, body JSON, created) — insert-only, latest per (userID, answered)
- [x] `parse_template(text) -> list[{type, label, options}]` (pure fn) + test/test_journal_template.py
- [x] Entry JSON is self-describing: `[{"label","type","options","value"}, ...]` — past entries render from their own JSON, so template edits only affect days with no entry yet
- [x] Routes: `GET /journal/template` (textarea + syntax help), `POST /journal/template/update/post`, `POST /journal/entry/update/post`
- [x] journal_index.html: template form above existing day-of-year questions (both kept); footer link "Edit Template"
- [x] SPECIFICATION.md + schema.sql updated; browser-verify on dev
- [ ] Run migration on prod

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
