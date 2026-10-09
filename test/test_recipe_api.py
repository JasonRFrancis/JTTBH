"""
Unit Tests: recipe endpoints of the /api/v1 REST API
====================================================
Tests encode *why* the behaviour matters:

* The recipe table is insert-only, so GET must return only the newest version
  of each recipe; returning every row hands clients stale, duplicate recipes.
* PUT is how the nightly recipe importer repairs recipes that failed to parse.
  It must write a new version under the SAME recipeID (so favorites, images and
  links survive) and must not clobber fields the client didn't send.
* Writing needs the recipe write bit; a read-only key must be refused.

All DB access is mocked; no live database.

Run: pytest test/test_recipe_api.py -v
"""

import json
import pytest
from unittest.mock import MagicMock
from flask import Flask

import app.routes.api as api_module
import app.services.api_auth as auth_module
import app.models.recipe_model as recipe_module
from app.services.decorators import PERM_BOOKMARK, PERM_RECIPE

USER_ID = 'user-1'
RECIPE_ID = 'rec-1'
HEADERS = {'Authorization': 'Bearer test-key'}


def _current_row(**over):
    row = {
        'recipeID': RECIPE_ID, 'title': 'Onion Tart', 'type': None, 'servings': None,
        'prep_time': None, 'cook_time': None, 'source': 'https://example.com/tart',
        'ingredients': '[]', 'directions': '[]', 'notes': None,
        'favorite': 1, 'want_to_try': 0, 'archived': 0, 'position': 3, 'created': None,
    }
    row.update(over)
    return row


@pytest.fixture
def db(monkeypatch):
    mock = MagicMock()
    mock.write_perm = PERM_RECIPE
    mock.current = _current_row()

    def execute_one(sql, params=None):
        if 'FROM api_key' in sql:
            return {'id': 1, 'userID': USER_ID,
                    'permissions': json.dumps({'read': PERM_RECIPE | PERM_BOOKMARK, 'write': mock.write_perm})}
        if 'SELECT username FROM user' in sql:
            return {'username': 'jason'}
        if 'SELECT userID FROM user' in sql:
            return {'userID': USER_ID}
        if 'COUNT(*)' in sql:
            return {'total': 0}
        if 'FROM recipe r' in sql:
            return dict(mock.current) if mock.current else None
        return None

    mock.execute_one.side_effect = execute_one
    mock.execute_query.side_effect = lambda sql, params=None: [dict(mock.current)]
    mock.execute_insert.side_effect = lambda sql, params=None: 1
    mock.execute_update.side_effect = lambda sql, params=None: 1
    for module in (api_module, auth_module, recipe_module):
        monkeypatch.setattr(module, 'db_manager', mock)
    return mock


@pytest.fixture
def client():
    flask_app = Flask(__name__)
    flask_app.config['TESTING'] = True
    flask_app.register_blueprint(api_module.api_bp, url_prefix='/api/v1')
    return flask_app.test_client()


def _inserted_values(db):
    """Params of the single recipe INSERT the request made."""
    calls = [c for c in db.execute_insert.call_args_list if 'INSERT INTO recipe' in c.args[0]]
    assert len(calls) == 1
    return calls[0].args[1]


class TestGetRecipes:
    def test_reads_current_version_only(self, client, db):
        resp = client.get('/api/v1/jason/recipes', headers=HEADERS)
        assert resp.status_code == 200
        sql = db.execute_query.call_args.args[0]
        assert 'MAX(r2.id)' in sql

    def test_returns_flags_and_parsed_lists(self, client, db):
        db.current = _current_row(ingredients='[{"amount":"1","unit":"cup","item":"flour","note":""}]',
                                  archived=1)
        rec = client.get('/api/v1/jason/recipes', headers=HEADERS).get_json()['data']['recipes'][0]
        assert rec['ingredients'][0]['unit'] == 'cup'
        assert rec['archived'] == 1


class TestBookmarkFilter:
    """The importer must see recipe-tagged bookmarks even after they're read."""

    def _count_sql(self, db):
        return next(c.args[0] for c in db.execute_one.call_args_list if 'COUNT(*)' in c.args[0])

    def test_unread_only_by_default(self, client, db):
        client.get('/api/v1/jason/bookmarks?tag=recipe', headers=HEADERS)
        assert '`read` = 0' in self._count_sql(db)

    def test_include_read(self, client, db):
        client.get('/api/v1/jason/bookmarks?tag=recipe&include_read=1', headers=HEADERS)
        assert '`read` = 0' not in self._count_sql(db)


class TestUpdateRecipe:
    def test_writes_new_version_with_same_id(self, client, db):
        body = {'ingredients': [{'amount': '0.5', 'unit': 'cup', 'item': 'flour', 'note': ''}],
                'directions': ['Mix.'], 'type': 'Breads & Muffins'}
        resp = client.put(f'/api/v1/jason/recipes/{RECIPE_ID}', json=body, headers=HEADERS)
        assert resp.status_code == 200
        vals = _inserted_values(db)
        assert vals[0] == RECIPE_ID
        assert vals[4] == 'Breads & Muffins'
        assert json.loads(vals[8])[0]['item'] == 'flour'
        assert json.loads(vals[9]) == ['Mix.']

    def test_omitted_fields_and_flags_carry_over(self, client, db):
        client.put(f'/api/v1/jason/recipes/{RECIPE_ID}', json={'type': 'Poultry'}, headers=HEADERS)
        vals = _inserted_values(db)
        assert vals[2] == 'Onion Tart'                  # title kept
        assert vals[3] == 'https://example.com/tart'    # source kept
        assert vals[11] == 3 and vals[12] == 1          # position, favorite kept

    def test_can_archive(self, client, db):
        client.put(f'/api/v1/jason/recipes/{RECIPE_ID}', json={'archived': True}, headers=HEADERS)
        assert _inserted_values(db)[14] == 1

    def test_unknown_recipe_is_404(self, client, db):
        db.current = None
        resp = client.put('/api/v1/jason/recipes/nope', json={'type': 'x'}, headers=HEADERS)
        assert resp.status_code == 404

    def test_rejects_non_list_ingredients(self, client, db):
        resp = client.put(f'/api/v1/jason/recipes/{RECIPE_ID}', json={'ingredients': '2 eggs'},
                          headers=HEADERS)
        assert resp.status_code == 400
        db.execute_insert.assert_not_called()

    def test_rejects_blank_title(self, client, db):
        # A NULL title is the soft-delete marker; a blank PUT must not delete.
        resp = client.put(f'/api/v1/jason/recipes/{RECIPE_ID}', json={'title': '  '}, headers=HEADERS)
        assert resp.status_code == 400

    def test_requires_recipe_write_permission(self, client, db):
        db.write_perm = 0
        resp = client.put(f'/api/v1/jason/recipes/{RECIPE_ID}', json={'type': 'x'}, headers=HEADERS)
        assert resp.status_code == 403
        db.execute_insert.assert_not_called()
