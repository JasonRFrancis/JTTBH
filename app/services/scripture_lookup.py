"""
Scripture text lookup service.

Lazily loads the five standard-works JSON files from app/data/scriptures/
and builds a flat reference→text index on first use.

Public API
----------
    lookup(ref: str) -> str | None
        Returns verse text for a reference like "John 3:16" or
        "1 Nephi 3:7-9" (range), or None if not found.
"""

import json
import os
import re
import threading

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'scriptures')

# Flat index: canonical reference string → verse text
# e.g. "John 3:16" → "For God so loved the world..."
_index: dict[str, str] = {}
_loaded = False
_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Book name aliases → canonical dataset name
# ---------------------------------------------------------------------------

_ALIASES: dict[str, str] = {
    # Old Testament
    'gen': 'Genesis', 'gen.': 'Genesis',
    'ex': 'Exodus', 'ex.': 'Exodus', 'exod': 'Exodus', 'exod.': 'Exodus',
    'lev': 'Leviticus', 'lev.': 'Leviticus',
    'num': 'Numbers', 'num.': 'Numbers',
    'deut': 'Deuteronomy', 'deut.': 'Deuteronomy', 'deu': 'Deuteronomy',
    'josh': 'Joshua', 'josh.': 'Joshua',
    'judg': 'Judges', 'judg.': 'Judges', 'jud': 'Judges',
    '1 sam': '1 Samuel', '1 sam.': '1 Samuel',
    '2 sam': '2 Samuel', '2 sam.': '2 Samuel',
    '1 kgs': '1 Kings', '1 kgs.': '1 Kings', '1 kings': '1 Kings',
    '2 kgs': '2 Kings', '2 kgs.': '2 Kings', '2 kings': '2 Kings',
    '1 chr': '1 Chronicles', '1 chr.': '1 Chronicles', '1 chron': '1 Chronicles',
    '2 chr': '2 Chronicles', '2 chr.': '2 Chronicles', '2 chron': '2 Chronicles',
    'neh': 'Nehemiah', 'neh.': 'Nehemiah',
    'esth': 'Esther', 'esth.': 'Esther',
    'ps': 'Psalms', 'ps.': 'Psalms', 'psa': 'Psalms', 'psalm': 'Psalms',
    'prov': 'Proverbs', 'prov.': 'Proverbs',
    'eccl': 'Ecclesiastes', 'eccl.': 'Ecclesiastes', 'ec': 'Ecclesiastes',
    'song': "Solomon's Song", 'song.': "Solomon's Song",
    'song of solomon': "Solomon's Song", 'sos': "Solomon's Song",
    "solomon's song": "Solomon's Song",
    'isa': 'Isaiah', 'isa.': 'Isaiah',
    'jer': 'Jeremiah', 'jer.': 'Jeremiah',
    'lam': 'Lamentations', 'lam.': 'Lamentations',
    'ezek': 'Ezekiel', 'ezek.': 'Ezekiel', 'ezk': 'Ezekiel',
    'dan': 'Daniel', 'dan.': 'Daniel',
    'hos': 'Hosea', 'hos.': 'Hosea',
    'obad': 'Obadiah', 'obad.': 'Obadiah',
    'jon': 'Jonah', 'jon.': 'Jonah',
    'mic': 'Micah', 'mic.': 'Micah',
    'nah': 'Nahum', 'nah.': 'Nahum',
    'hab': 'Habakkuk', 'hab.': 'Habakkuk',
    'zeph': 'Zephaniah', 'zeph.': 'Zephaniah',
    'hag': 'Haggai', 'hag.': 'Haggai',
    'zech': 'Zechariah', 'zech.': 'Zechariah',
    'mal': 'Malachi', 'mal.': 'Malachi',

    # New Testament
    'matt': 'Matthew', 'matt.': 'Matthew', 'mt': 'Matthew', 'mt.': 'Matthew',
    'mk': 'Mark', 'mk.': 'Mark',
    'lk': 'Luke', 'lk.': 'Luke',
    'acts': 'Acts',
    'rom': 'Romans', 'rom.': 'Romans',
    '1 cor': '1 Corinthians', '1 cor.': '1 Corinthians',
    '2 cor': '2 Corinthians', '2 cor.': '2 Corinthians',
    'gal': 'Galatians', 'gal.': 'Galatians',
    'eph': 'Ephesians', 'eph.': 'Ephesians',
    'philip': 'Philippians', 'philip.': 'Philippians',
    'phil': 'Philippians', 'phil.': 'Philippians',
    'col': 'Colossians', 'col.': 'Colossians',
    '1 thes': '1 Thessalonians', '1 thes.': '1 Thessalonians',
    '1 thess': '1 Thessalonians', '1 thess.': '1 Thessalonians',
    '2 thes': '2 Thessalonians', '2 thes.': '2 Thessalonians',
    '2 thess': '2 Thessalonians', '2 thess.': '2 Thessalonians',
    '1 tim': '1 Timothy', '1 tim.': '1 Timothy',
    '2 tim': '2 Timothy', '2 tim.': '2 Timothy',
    'philem': 'Philemon', 'philem.': 'Philemon', 'phlm': 'Philemon',
    'heb': 'Hebrews', 'heb.': 'Hebrews',
    'jas': 'James', 'jas.': 'James',
    '1 pet': '1 Peter', '1 pet.': '1 Peter',
    '2 pet': '2 Peter', '2 pet.': '2 Peter',
    '1 jn': '1 John', '1 jn.': '1 John',
    '2 jn': '2 John', '2 jn.': '2 John',
    '3 jn': '3 John', '3 jn.': '3 John',
    'rev': 'Revelation', 'rev.': 'Revelation',

    # Book of Mormon
    '1 ne': '1 Nephi', '1 ne.': '1 Nephi', '1ne': '1 Nephi',
    '2 ne': '2 Nephi', '2 ne.': '2 Nephi', '2ne': '2 Nephi',
    'w of m': 'Words of Mormon', 'wom': 'Words of Mormon',
    'hel': 'Helaman', 'hel.': 'Helaman',
    '3 ne': '3 Nephi', '3 ne.': '3 Nephi', '3ne': '3 Nephi',
    '4 ne': '4 Nephi', '4 ne.': '4 Nephi', '4ne': '4 Nephi',
    'morm': 'Mormon', 'morm.': 'Mormon',
    'moro': 'Moroni', 'moro.': 'Moroni',

    # Pearl of Great Price
    'abr': 'Abraham', 'abr.': 'Abraham',
    'js-m': 'Joseph Smith—Matthew', 'js—m': 'Joseph Smith—Matthew',
    'jsm': 'Joseph Smith—Matthew', 'joseph smith-matthew': 'Joseph Smith—Matthew',
    'joseph smith--matthew': 'Joseph Smith—Matthew',
    'js-h': 'Joseph Smith—History', 'js—h': 'Joseph Smith—History',
    'jsh': 'Joseph Smith—History', 'joseph smith-history': 'Joseph Smith—History',
    'joseph smith--history': 'Joseph Smith—History',
    'a of f': 'Articles of Faith', 'af': 'Articles of Faith',

    # D&C variants
    'doctrine and covenants': 'D&C',
    'doc. and cov.': 'D&C',
    'doc and cov': 'D&C',
    'd & c': 'D&C',
}

# Lowercase canonical names → canonical (for identity lookup)
_CANONICAL = {name.lower(): name for name in [
    'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
    'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
    '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles',
    'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs',
    'Ecclesiastes', "Solomon's Song", 'Isaiah', 'Jeremiah',
    'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos',
    'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah',
    'Haggai', 'Zechariah', 'Malachi',
    'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans',
    '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
    'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
    '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews',
    'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John',
    'Jude', 'Revelation',
    '1 Nephi', '2 Nephi', 'Jacob', 'Enos', 'Jarom', 'Omni',
    'Words of Mormon', 'Mosiah', 'Alma', 'Helaman',
    '3 Nephi', '4 Nephi', 'Mormon', 'Ether', 'Moroni',
    'D&C',
    'Moses', 'Abraham', 'Joseph Smith—Matthew', 'Joseph Smith—History',
    'Articles of Faith',
]}


def _normalize_book(name: str) -> str | None:
    """Return canonical book name or None if unrecognized."""
    key = name.strip().lower()
    if key in _CANONICAL:
        return _CANONICAL[key]
    if key in _ALIASES:
        return _ALIASES[key]
    return None


# ---------------------------------------------------------------------------
# Index building
# ---------------------------------------------------------------------------

def _build_index() -> None:
    global _index, _loaded

    idx: dict[str, str] = {}

    volumes = [
        ('old-testament.json',        'books'),
        ('new-testament.json',         'books'),
        ('book-of-mormon.json',        'books'),
        ('pearl-of-great-price.json',  'books'),
    ]

    for fname, _ in volumes:
        path = os.path.join(_DATA_DIR, fname)
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        for book in data['books']:
            for chapter in book['chapters']:
                for verse in chapter['verses']:
                    idx[verse['reference']] = verse['text']

    # D&C uses sections, not books
    dc_path = os.path.join(_DATA_DIR, 'doctrine-and-covenants.json')
    if os.path.exists(dc_path):
        with open(dc_path, encoding='utf-8') as f:
            dc = json.load(f)
        for section in dc['sections']:
            for verse in section['verses']:
                idx[verse['reference']] = verse['text']

    _index = idx
    _loaded = True


def _ensure_loaded() -> None:
    global _loaded
    if not _loaded:
        with _lock:
            if not _loaded:
                _build_index()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Reference pattern: "Book Name chapter:verse" or "Book Name chapter:start-end"
_REF_RE = re.compile(
    r'^(.+?)\s+(\d+):(\d+)(?:\s*[-–—]\s*(\d+))?$',
    re.IGNORECASE,
)


def lookup(ref: str) -> str | None:
    """
    Look up scripture text by reference.

    Handles single verses ("John 3:16") and ranges ("1 Nephi 3:7-9").
    Returns the verse text (joined by a space for ranges), or None if
    the reference cannot be resolved.
    """
    _ensure_loaded()

    ref = ref.strip()

    # Try the index directly first (handles exact canonical refs)
    if ref in _index:
        return _index[ref]

    m = _REF_RE.match(ref)
    if not m:
        return None

    raw_book    = m.group(1).strip()
    chapter     = int(m.group(2))
    verse_start = int(m.group(3))
    verse_end   = int(m.group(4)) if m.group(4) else verse_start

    book = _normalize_book(raw_book)
    if not book:
        return None

    texts = []
    for v in range(verse_start, verse_end + 1):
        candidate = f'{book} {chapter}:{v}'
        text = _index.get(candidate)
        if text:
            texts.append(text)

    return ' '.join(texts) if texts else None


def book_names() -> list[str]:
    """Return all canonical book names (for autocomplete or validation)."""
    return sorted(_CANONICAL.values())
