"""
Unit tests: journal template markup + entry values
==================================================
Why this matters:

* The template is free text typed into a textarea; every line must become a
  usable field, so a typo degrades to a plain textarea rather than vanishing.
* Saved entries are self-describing JSON (label/type/options per item) — that
  is what lets a template edit leave past days untouched.
* Values written to the JSON column must be valid JSON of the right type
  (bool for checks, number for numbers, only listed options for choices).

Pure functions only; no database.

Run: pytest test/test_journal_template.py -v
"""

import json

from werkzeug.datastructures import MultiDict

from app.routes.journal import collect_values, parse_template


TEMPLATE = """
# Morning
What am I grateful for?
One word for today [line]
Hours slept [number]
Exercised? [check]
Energy [low| ok |high]

What did I read [today]?
Mystery [frobnicate]
"""


def test_parse_each_line_type():
    fields = parse_template(TEMPLATE)
    assert fields == [
        {'type': 'heading', 'label': 'Morning'},
        {'type': 'text', 'label': 'What am I grateful for?'},
        {'type': 'line', 'label': 'One word for today'},
        {'type': 'number', 'label': 'Hours slept'},
        {'type': 'check', 'label': 'Exercised?'},
        {'type': 'choice', 'label': 'Energy', 'options': ['low', 'ok', 'high']},
        # Brackets mid-line are part of the question, not a type.
        {'type': 'text', 'label': 'What did I read [today]?'},
        # Unknown type keeps the whole line so nothing the user wrote is lost.
        {'type': 'text', 'label': 'Mystery [frobnicate]'},
    ]


def test_empty_template_has_no_fields():
    assert parse_template('  \n\n') == []


def test_collect_values_types_and_validation():
    fields = parse_template(TEMPLATE)
    form = MultiDict({
        'f1': ' thankful ', 'f2': 'calm', 'f3': '7.5',
        'f4': '1', 'f5': 'ok',
    })
    out = collect_values(fields, form)
    assert out[0] == {'type': 'heading', 'label': 'Morning'}  # headings carry no value
    assert [o.get('value') for o in out[1:6]] == ['thankful', 'calm', 7.5, True, 'ok']
    assert out[5]['options'] == ['low', 'ok', 'high']  # entry keeps its own options

    # Unchecked box, junk number, forged choice → safe values; integers stay ints.
    out = collect_values(fields, MultiDict({'f3': 'nan', 'f5': 'bogus'}))
    assert out[3]['value'] is None and out[4]['value'] is False and out[5]['value'] is None
    assert collect_values(fields, MultiDict({'f3': '8'}))[3]['value'] == 8
    json.dumps(out, allow_nan=False)  # must be storable in a MySQL JSON column


def test_resave_replaces_old_values():
    # A saved entry's fields (with values) are re-fed on the next save.
    saved = collect_values(parse_template('Q [line]'), MultiDict({'f0': 'old'}))
    assert collect_values(saved, MultiDict({'f0': 'new'})) == [
        {'type': 'line', 'label': 'Q', 'value': 'new'}
    ]
