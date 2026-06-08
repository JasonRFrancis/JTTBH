"""
Report recipes with missing data (no ingredients, no directions, etc).

Writes a human-readable report to claude/recipe_problems.txt and a JSON list
of problem URLs to claude/recipe_problems.json for easy re-import.

Usage:
    python claude/find_recipe_problems.py [--user-id UUID]
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

REPORT_TXT  = os.path.join(os.path.dirname(__file__), 'recipe_problems.txt')
REPORT_JSON = os.path.join(os.path.dirname(__file__), 'recipe_problems.json')
FAILURES_LOG = os.path.join(os.path.dirname(__file__), 'import_failures.json')


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--user-id')
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    from app import create_app
    from app.services.database import db_manager

    app = create_app()
    with app.app_context():
        user_id = args.user_id
        if not user_id:
            users = db_manager.execute_query("SELECT userID, username FROM user ORDER BY username", ())
            if not users:
                print('No users found.')
                sys.exit(1)
            print('Select user:')
            for i, u in enumerate(users):
                print(f"  {i+1}. {u['username']} ({u['userID']})")
            user_id = users[int(input('Enter number: ').strip()) - 1]['userID']

        rows = db_manager.execute_query("""
            SELECT r.recipeID, r.title, r.source, r.ingredients, r.directions, r.notes
            FROM recipe r
            WHERE r.userID = %s
              AND r.id = (SELECT MAX(r2.id) FROM recipe r2 WHERE r2.recipeID = r.recipeID)
              AND r.title IS NOT NULL
            ORDER BY r.title
        """, (user_id,))

        known_failures = set()
        if os.path.exists(FAILURES_LOG):
            with open(FAILURES_LOG) as f:
                known_failures = set(json.load(f).keys())

        no_content     = []  # neither ingredients nor directions
        no_ingredients = []  # has directions but no ingredients
        no_directions  = []  # has ingredients but no directions
        no_images      = []  # check separately via recipe_image table

        image_counts = {}
        image_rows = db_manager.execute_query(
            "SELECT recipeID, COUNT(*) AS n FROM recipe_image WHERE userID = %s GROUP BY recipeID",
            (user_id,),
        )
        for row in image_rows:
            image_counts[row['recipeID']] = row['n']

        for r in rows:
            ingredients = json.loads(r['ingredients']) if r.get('ingredients') else []
            directions  = json.loads(r['directions'])  if r.get('directions')  else []
            has_ing = bool(ingredients)
            has_dir = bool(directions)

            if not has_ing and not has_dir:
                no_content.append(r)
            elif not has_ing:
                no_ingredients.append(r)
            elif not has_dir:
                no_directions.append(r)

            if not image_counts.get(r['recipeID']):
                no_images.append(r)

        lines = []
        lines.append(f"Recipe problems report — {len(rows)} total recipes\n")
        lines.append(f"  No content (no ingredients AND no directions): {len(no_content)}")
        lines.append(f"  Missing ingredients only:                      {len(no_ingredients)}")
        lines.append(f"  Missing directions only:                       {len(no_directions)}")
        lines.append(f"  No images:                                     {len(no_images)}")
        lines.append(f"  Known import failures (import_failures.json):  {len(known_failures)}")
        lines.append('')

        sections = [
            ('NO CONTENT — nothing was extracted at import time', no_content),
            ('MISSING INGREDIENTS', no_ingredients),
            ('MISSING DIRECTIONS', no_directions),
        ]
        for label, group in sections:
            if not group:
                continue
            lines.append(f'--- {label} ({len(group)}) ---')
            for r in group:
                flag = ' [known failure]' if r.get('source') in known_failures else ''
                lines.append(f"  {r['title'][:70]}{flag}")
                if r.get('source'):
                    lines.append(f"    {r['source']}")
                lines.append(f"    ID: {r['recipeID']}")
            lines.append('')

        report = '\n'.join(lines)
        print(report)

        with open(REPORT_TXT, 'w') as f:
            f.write(report)

        # JSON output: just the problem URLs grouped by type, for re-import or scripting
        problem_urls = {
            'no_content':     [r['source'] for r in no_content     if r.get('source')],
            'no_ingredients': [r['source'] for r in no_ingredients if r.get('source')],
            'no_directions':  [r['source'] for r in no_directions  if r.get('source')],
        }
        with open(REPORT_JSON, 'w') as f:
            json.dump(problem_urls, f, indent=2)

        print(f'Report written to {REPORT_TXT}')
        print(f'URL lists written to {REPORT_JSON}')


if __name__ == '__main__':
    main()
