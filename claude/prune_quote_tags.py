#!/usr/bin/env python3
"""
Prune quote tags that aren't on the topic master list.

The quote feature now draws tag suggestions from the same master topic list
as the study feature (see TopicModel.get_all). Existing quotes may have
tags typed before that list existed; this drops any tag not on the list from
each quote (insert-only — writes a new revision row, doesn't touch history).

Run from project root:
    python3 claude/prune_quote_tags.py
    python3 claude/prune_quote_tags.py --dry-run
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.quote_model import QuoteModel
from app.services.database import db_manager


def get_tagged_quotes():
    return db_manager.execute_query("""
        SELECT q.quoteID, q.userID, q.body, q.author, q.title, q.source, q.tags
        FROM quote q
        WHERE q.id = (SELECT MAX(q2.id) FROM quote q2 WHERE q2.quoteID = q.quoteID)
          AND q.body IS NOT NULL
          AND q.tags IS NOT NULL
          AND q.tags != ''
    """, ())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Print without writing')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        master = {row['name'].lower() for row in db_manager.execute_query('SELECT name FROM topic', ())}
        quotes = get_tagged_quotes()

        changed = 0
        for q in quotes:
            tags = [t.strip() for t in q['tags'].split(',') if t.strip()]
            kept = [t for t in tags if t.lower() in master]
            dropped = [t for t in tags if t.lower() not in master]
            if not dropped:
                continue
            changed += 1
            print(f"  {q['quoteID'][:8]} drop {dropped} keep {kept}")
            if not args.dry_run:
                QuoteModel.update(
                    q['userID'], q['quoteID'], q['body'], q['author'] or '',
                    q['title'] or '', q['source'] or '', ', '.join(kept),
                )

        verb = 'Would update' if args.dry_run else 'Updated'
        print(f"\n{verb} {changed} of {len(quotes)} tagged quotes.")


if __name__ == '__main__':
    main()
