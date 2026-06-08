"""
Parse amount/unit out of raw ingredient text, detect subtitles, and
standardise units across all recipes in the DB.

Applies to ingredients where amount == '' and unit == '', which is what
the Pinboard/JSON-LD importer produces. Existing fully-parsed ingredients
(amount already set) only have their unit standardised.

Usage:
    python claude/migrate_ingredients.py [--dry-run] [--user-id UUID]

Writes a new recipe row (insert-only table) only when the ingredients JSON
actually changed.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--user-id', help='Limit to one user UUID')
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    from app import create_app
    from app.services.database import db_manager
    from app.services.recipe_utils import parse_ingredient_text, standardize_unit, parse_amount_input

    app = create_app()
    with app.app_context():
        if args.user_id:
            user_ids = [args.user_id]
        else:
            user_ids = [r['userID'] for r in db_manager.execute_query("SELECT userID FROM user", ())]

        total = updated = skipped = errors = 0

        for user_id in user_ids:
            rows = db_manager.execute_query("""
                SELECT r.id, r.recipeID, r.title, r.ingredients
                FROM recipe r
                WHERE r.userID = %s
                  AND r.id = (SELECT MAX(r2.id) FROM recipe r2 WHERE r2.recipeID = r.recipeID)
                  AND r.title IS NOT NULL
            """, (user_id,))

            for row in rows:
                total += 1
                try:
                    ings = json.loads(row['ingredients']) if row['ingredients'] else []
                except json.JSONDecodeError:
                    print(f"  ERROR (bad JSON): {row['title'][:60]}")
                    errors += 1
                    continue

                new_ings = []
                changed = False

                for ing in ings:
                    if 'subtitle' in ing:
                        new_ings.append(ing)
                        continue

                    amount = ing.get('amount', '')
                    unit = ing.get('unit', '')
                    item = ing.get('item', '')
                    note = ing.get('note', '')

                    if not amount and not unit and item:
                        # Unparsed: try to extract amount/unit/subtitle from item text
                        parsed = parse_ingredient_text(item)
                        if 'subtitle' in parsed:
                            new_ings.append(parsed)
                            changed = True
                        else:
                            merged = {
                                'amount': parsed['amount'],
                                'unit': parsed['unit'] or standardize_unit(unit),
                                'item': parsed['item'] if parsed['item'] else item,
                                'note': parsed['note'] if parsed['note'] else note,
                            }
                            if merged != {'amount': amount, 'unit': unit, 'item': item, 'note': note}:
                                changed = True
                            new_ings.append(merged)
                    else:
                        # Already parsed: just standardise unit and normalise amount to decimal
                        new_unit = standardize_unit(unit)
                        new_amount = parse_amount_input(amount) if amount else ''
                        merged = {'amount': new_amount, 'unit': new_unit, 'item': item, 'note': note}
                        if merged != {'amount': amount, 'unit': unit, 'item': item, 'note': note}:
                            changed = True
                        new_ings.append(merged)

                if not changed:
                    skipped += 1
                    continue

                updated += 1
                print(f"  {'(dry) ' if args.dry_run else ''}UPDATE: {row['title'][:70]}")

                if not args.dry_run:
                    db_manager.execute_insert("""
                        INSERT INTO recipe
                          (recipeID, userID, title, source, type, servings, prep_time, cook_time,
                           ingredients, directions, notes, position, favorite, want_to_try, created, created_by)
                        SELECT
                          recipeID, userID, title, source, type, servings, prep_time, cook_time,
                          %s, directions, notes, position, favorite, want_to_try, NOW(), created_by
                        FROM recipe WHERE id = %s
                    """, (json.dumps(new_ings, ensure_ascii=False), row['id']))

        print(f'\n{"DRY RUN — " if args.dry_run else ""}Done.')
        print(f'  Recipes scanned:  {total}')
        print(f'  Updated:          {updated}')
        print(f'  Already clean:    {skipped}')
        print(f'  Errors:           {errors}')


if __name__ == '__main__':
    main()
