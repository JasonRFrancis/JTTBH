"""
Unit Tests: recipe amount ranges
================================
The recipe importer stores ranges ('2-3 cloves') as 'low-high' decimals; they
must display as fractions and survive an edit round trip.

Run: pytest test/test_recipe_amount_range.py -v
"""

from app.services.recipe_utils import format_amount, parse_amount_input


class TestAmountRanges:
    def test_whole_number_with_unicode_fraction(self):
        # Regression: '2½' used to become '21/2' and be stored as 10.5
        assert parse_amount_input('2½') == '2.5'

    def test_format_range(self):
        assert format_amount('2.5-3') == '2½–3'

    def test_parse_range_input(self):
        assert parse_amount_input('2½–3') == '2.5-3'
        assert parse_amount_input('1 to 2') == '1-2'

    def test_round_trip(self):
        assert parse_amount_input(format_amount('0.5-1')) == '0.5-1'
