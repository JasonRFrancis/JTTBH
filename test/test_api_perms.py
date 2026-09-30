"""
API read permissions
====================
Why this matters: an API key is granted specific feature bits. A key minted for the
project agent (read=64) must not be able to read the owner's todos, bookmarks, recipes
or meals just because it is a valid key for that user. Every GET must check its bit.

DB access is mocked; no live database.

Run: pytest test/test_api_perms.py -v
"""
import json
from unittest.mock import MagicMock

import pytest

from app import create_app
from app.services.decorators import PERM_PROJECT

USER_ID = 'u-1'


@pytest.fixture
def client(monkeypatch):
    db = MagicMock()

    def execute_one(sql, params=None):
        if 'FROM api_key' in sql:
            return {'id': 1, 'userID': USER_ID, 'permissions': json.dumps({'read': PERM_PROJECT, 'write': 0})}
        if 'SELECT username FROM user' in sql:
            return {'username': 'jason'}
        if 'SELECT userID FROM user' in sql:
            return {'userID': USER_ID}
        return None

    db.execute_one.side_effect = execute_one
    db.execute_query.return_value = []
    for mod in ('app.services.api_auth', 'app.routes.api', 'app.models.project_model', 'app.models.meal_model'):
        monkeypatch.setattr(f'{mod}.db_manager', db)
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


H = {'Authorization': 'Bearer test'}


@pytest.mark.parametrize('path', [
    '/api/v1/jason/todos',
    '/api/v1/jason/bookmarks',
    '/api/v1/jason/recipes',
    '/api/v1/jason/fitness',
    '/api/v1/jason/meals',
    '/api/v1/jason/food/0074261182164',
])
def test_project_only_key_cannot_read_other_features(client, path):
    r = client.get(path, headers=H)
    assert r.status_code == 403, (path, r.get_json())


def test_project_only_key_can_still_read_projects(client):
    assert client.get('/api/v1/jason/projects', headers=H).status_code == 200


def test_key_cannot_read_another_users_projects(client):
    assert client.get('/api/v1/someoneelse/projects', headers=H).status_code == 403
