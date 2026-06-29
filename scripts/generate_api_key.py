#!/usr/bin/env python3
"""
Generate an API key for the JTTBH Hermes Agent.

Usage (from project root):
    python scripts/generate_api_key.py

The raw key is printed once and never stored. Keep it secret.
"""

import json
import os
import sys
import uuid

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('FLASK_ENV', 'production')

from app.services.api_auth import generate_key
from app.services.database import db_manager


def main():
    name     = input('Key name (e.g. hermes-agent): ').strip()
    username = input('Username: ').strip()

    if not name or not username:
        print('Error: name and username are required.')
        sys.exit(1)

    user = db_manager.execute_one(
        '''
        SELECT u.userID, up.read AS perm_read, up.write AS perm_write
        FROM user u
        LEFT JOIN user_permission up
            ON up.id = (
                SELECT id FROM user_permission
                WHERE userID = u.userID
                ORDER BY created DESC, id DESC
                LIMIT 1
            )
        WHERE u.username = %s
        ''',
        (username,),
    )

    if not user:
        print(f'Error: user "{username}" not found.')
        sys.exit(1)

    perm_read  = int(user['perm_read']  or 0)
    perm_write = int(user['perm_write'] or 0)
    permissions = json.dumps({'read': perm_read, 'write': perm_write})

    raw_key, key_hash = generate_key()
    key_id = str(uuid.uuid4())

    db_manager.execute_insert(
        '''INSERT INTO api_key
               (keyID, userID, key_hash, key_name, permissions, active, created, created_by)
           VALUES (%s, %s, %s, %s, %s, 1, NOW(), %s)''',
        (key_id, user['userID'], key_hash, name, permissions, user['userID']),
    )

    print()
    print('=' * 60)
    print(f'  API key created for: {username}')
    print(f'  Name: {name}')
    print()
    print(f'  KEY: {raw_key}')
    print()
    print('  Store this key securely — it will NOT be shown again.')
    print('=' * 60)


if __name__ == '__main__':
    main()
