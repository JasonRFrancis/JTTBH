"""
Shared utilities for recipe ingredient parsing and display.
"""
import re
from fractions import Fraction

# ---------------------------------------------------------------------------
# Unit standardisation map
# ---------------------------------------------------------------------------

_UNIT_MAP: dict[str, str] = {
    # tablespoon
    'tablespoon': 'tbsp', 'tablespoons': 'tbsp',
    'tbsp': 'tbsp', 'tbsps': 'tbsp', 'tbs': 'tbsp', 'T': 'tbsp',
    # teaspoon
    'teaspoon': 'tsp', 'teaspoons': 'tsp',
    'tsp': 'tsp', 'tsps': 'tsp', 't': 'tsp',
    # cup
    'cup': 'cup', 'cups': 'cup', 'c': 'cup',
    # fluid ounce (before plain ounce so the two-word form wins)
    'fl oz': 'fl oz', 'fl. oz.': 'fl oz', 'fl. oz': 'fl oz',
    'fluid ounce': 'fl oz', 'fluid ounces': 'fl oz',
    # ounce
    'ounce': 'oz', 'ounces': 'oz', 'oz': 'oz', 'oz.': 'oz',
    # pound
    'pound': 'lb', 'pounds': 'lb', 'lb': 'lb', 'lbs': 'lb',
    # gram / kilogram
    'gram': 'g', 'grams': 'g', 'g': 'g',
    'kilogram': 'kg', 'kilograms': 'kg', 'kg': 'kg',
    # milliliter / liter
    'milliliter': 'ml', 'milliliters': 'ml',
    'millilitre': 'ml', 'millilitres': 'ml', 'ml': 'ml', 'mL': 'ml',
    'liter': 'L', 'liters': 'L', 'litre': 'L', 'litres': 'L', 'L': 'L', 'l': 'L',
    # pint / quart / gallon
    'pint': 'pt', 'pints': 'pt', 'pt': 'pt',
    'quart': 'qt', 'quarts': 'qt', 'qt': 'qt',
    'gallon': 'gal', 'gallons': 'gal', 'gal': 'gal',
    # counting / container units
    'package': 'pkg', 'packages': 'pkg', 'pkg': 'pkg',
    'can': 'can', 'cans': 'can',
    'jar': 'jar', 'jars': 'jar',
    'bag': 'bag', 'bags': 'bag',
    'bottle': 'bottle', 'bottles': 'bottle',
    'box': 'box', 'boxes': 'box',
    'sheet': 'sheet', 'sheets': 'sheet',
    'slice': 'slice', 'slices': 'slice',
    'piece': 'piece', 'pieces': 'piece',
    'stick': 'stick', 'sticks': 'stick',
    # ingredient-specific counting
    'clove': 'clove', 'cloves': 'clove',
    'sprig': 'sprig', 'sprigs': 'sprig',
    'stalk': 'stalk', 'stalks': 'stalk',
    'bunch': 'bunch', 'bunches': 'bunch',
    'head': 'head', 'heads': 'head',
    'bulb': 'bulb', 'bulbs': 'bulb',
    # small measures
    'pinch': 'pinch', 'pinches': 'pinch',
    'dash': 'dash', 'dashes': 'dash',
    'drop': 'drop', 'drops': 'drop',
    'handful': 'handful', 'handfuls': 'handful',
    # size descriptors kept as-is
    'inch': 'inch', 'inches': 'inch',
}


def standardize_unit(unit: str) -> str:
    """Return canonical unit form, or the input unchanged if unknown."""
    if not unit:
        return ''
    return _UNIT_MAP.get(unit) or _UNIT_MAP.get(unit.lower()) or unit


# ---------------------------------------------------------------------------
# Unicode fraction helpers
# ---------------------------------------------------------------------------

_UNICODE_TO_ASCII: dict[str, str] = {
    '¼': '1/4', '½': '1/2', '¾': '3/4',
    '⅓': '1/3', '⅔': '2/3',
    '⅛': '1/8', '⅜': '3/8', '⅝': '5/8', '⅞': '7/8',
    '⅙': '1/6', '⅚': '5/6',
    '⅕': '1/5', '⅖': '2/5', '⅗': '3/5', '⅘': '4/5',
}

_FRAC_TO_UNICODE: dict[Fraction, str] = {
    Fraction(1, 4): '¼', Fraction(1, 2): '½', Fraction(3, 4): '¾',
    Fraction(1, 3): '⅓', Fraction(2, 3): '⅔',
    Fraction(1, 8): '⅛', Fraction(3, 8): '⅜', Fraction(5, 8): '⅝', Fraction(7, 8): '⅞',
    Fraction(1, 6): '⅙', Fraction(5, 6): '⅚',
    Fraction(1, 5): '⅕', Fraction(2, 5): '⅖', Fraction(3, 5): '⅗', Fraction(4, 5): '⅘',
}

# Matches a leading number in an ingredient string.
# Groups: (plain numeric OR fraction), optional unicode frac suffix
_AMOUNT_RE = re.compile(
    r'^(\d+(?:\.\d+)?(?:\s+\d+/\d+)?|\d+/\d+)'
    r'([¼½¾⅓⅔⅛⅜⅝⅞⅙⅚⅕⅖⅗⅘]?)'
)


def _to_decimal(s: str) -> str:
    """Convert a fraction string ('1/2', '1.5') to a normalised decimal string."""
    try:
        f = Fraction(s).limit_denominator(64)
        return str(f.numerator) if f.denominator == 1 else f'{float(f):.6g}'
    except (ValueError, ZeroDivisionError):
        return s


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_amount_input(value: str) -> str:
    """
    Convert user-typed amount ('1/2', '1 1/2', '¾', '0.5') to a decimal
    string suitable for DB storage.  Returns '' for blank/invalid input.
    """
    value = (value or '').strip()
    if not value:
        return ''
    # Expand unicode fractions
    for uc, asc in _UNICODE_TO_ASCII.items():
        value = value.replace(uc, asc)
    parts = value.split()
    try:
        f = Fraction(parts[0]) + Fraction(parts[1]) if len(parts) == 2 else Fraction(parts[0])
        f = f.limit_denominator(64)
        return str(f.numerator) if f.denominator == 1 else f'{float(f):.6g}'
    except (ValueError, ZeroDivisionError, IndexError):
        return value


def format_amount(value) -> str:
    """
    Convert a stored decimal amount ('0.5', '1.5') to a display string using
    unicode fractions where possible ('½', '1½').
    """
    if value is None or value == '' or value == 0:
        return ''
    s = str(value).strip()
    if not s:
        return ''
    try:
        f = Fraction(s).limit_denominator(16)
    except (ValueError, ZeroDivisionError):
        return s
    whole = int(f)
    frac = f - whole
    frac_str = _FRAC_TO_UNICODE.get(frac, f'{frac.numerator}/{frac.denominator}' if frac else '')
    if whole == 0:
        return frac_str or s
    return f'{whole}{frac_str}' if frac else str(whole)


def parse_ingredient_text(text: str) -> dict:
    """
    Parse a raw ingredient string like '1½ cups all-purpose flour, sifted'
    into {amount, unit, item, note}.

    Returns {subtitle: text} when the string looks like a section heading
    (no leading number and ends with ':').
    """
    text = text.strip()
    if not text:
        return {'amount': '', 'unit': '', 'item': '', 'note': ''}

    # Subtitle: no leading digit, ends with colon, no comma (to avoid
    # misclassifying real ingredients like "butter, room temperature:")
    if text.endswith(':') and not text[0].isdigit() and text[0] not in _UNICODE_TO_ASCII:
        inner = text[:-1].strip()
        if ',' not in inner and len(inner) < 60:
            return {'subtitle': inner}

    # Try to parse a leading amount
    amount = ''
    rest = text

    # Check for a lone unicode fraction at the start
    if text and text[0] in _UNICODE_TO_ASCII:
        amount = _to_decimal(_UNICODE_TO_ASCII[text[0]])
        rest = text[1:].strip()
    else:
        m = _AMOUNT_RE.match(text)
        if m:
            num_str = m.group(1).strip()
            uc_frac = m.group(2)
            rest = text[m.end():].strip()
            if uc_frac:
                try:
                    combined = Fraction(num_str.replace(' ', '+')) + Fraction(_UNICODE_TO_ASCII[uc_frac])
                    amount = _to_decimal(str(combined))
                except (ValueError, ZeroDivisionError):
                    amount = _to_decimal(num_str)
            else:
                amount = _to_decimal(num_str)

    # Try to match a unit word immediately after the amount
    unit = ''
    if rest:
        words = rest.split(None, 1)
        candidate = words[0].rstrip('.,')
        if candidate in _UNIT_MAP or candidate.lower() in _UNIT_MAP:
            unit = standardize_unit(candidate)
            rest = words[1].strip() if len(words) > 1 else ''

    # Split rest into item and note at first comma
    item, _, note = rest.partition(',')
    return {
        'amount': amount,
        'unit': unit,
        'item': item.strip(),
        'note': note.strip(),
    }
