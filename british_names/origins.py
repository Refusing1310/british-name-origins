"""Classify British place names by the linguistic origin of their elements.

British town and city names are built from recognisable prefixes and suffixes
that were contributed by successive settlers: Brittonic/Celtic speakers, the
Romans, the Anglo-Saxons (Old English), Scandinavian settlers (Old Norse) and
the Normans. The endings and beginnings of a name are a strong (if imperfect)
signal of which of these traditions produced it. For example ``-by`` and
``-thorpe`` are Old Norse, ``-ton`` and ``-ham`` are Old English, ``-chester``
descends from Latin *castra*, and ``pen-``/``tre-``/``aber-`` are Celtic.

The classification here is a transparent, rule-based heuristic. It is not
authoritative etymology, but it is good enough to colour a map and to serve as
a starting point that can later be refined against real gazetteer data.
"""

from __future__ import annotations

from enum import Enum
from typing import Tuple


class Origin(str, Enum):
    """Linguistic tradition a place-name element belongs to."""

    OLD_ENGLISH = "Old English"
    OLD_NORSE = "Old Norse"
    CELTIC = "Celtic / Brittonic"
    ROMAN = "Roman / Latin"
    NORMAN = "Norman French"
    UNKNOWN = "Unknown"


# RGB colours used for map dots and legends. Chosen to be distinct.
ORIGIN_COLORS: dict[Origin, Tuple[int, int, int]] = {
    Origin.OLD_ENGLISH: (31, 119, 180),   # blue
    Origin.OLD_NORSE: (214, 39, 40),       # red
    Origin.CELTIC: (44, 160, 44),          # green
    Origin.ROMAN: (148, 103, 189),         # purple
    Origin.NORMAN: (255, 127, 14),         # orange
    Origin.UNKNOWN: (127, 127, 127),       # grey
}


# Suffix rules, checked in order. The first match wins, so more specific or
# more diagnostic endings are listed before generic ones.
_SUFFIX_RULES: list[tuple[str, Origin]] = [
    # Old Norse -- Scandinavian settlement (the Danelaw, Cumbria, etc.)
    ("thwaite", Origin.OLD_NORSE),
    ("thorpe", Origin.OLD_NORSE),
    ("thorp", Origin.OLD_NORSE),
    ("toft", Origin.OLD_NORSE),
    ("kirk", Origin.OLD_NORSE),
    ("garth", Origin.OLD_NORSE),
    ("beck", Origin.OLD_NORSE),
    ("holme", Origin.OLD_NORSE),
    ("gill", Origin.OLD_NORSE),
    ("ness", Origin.OLD_NORSE),
    ("by", Origin.OLD_NORSE),

    # Roman / Latin -- from castra ("camp") and colonia.
    ("chester", Origin.ROMAN),
    ("caster", Origin.ROMAN),
    ("cester", Origin.ROMAN),

    # Old English -- the largest layer of English place names.
    ("borough", Origin.OLD_ENGLISH),
    ("brough", Origin.OLD_ENGLISH),
    ("bury", Origin.OLD_ENGLISH),
    ("bourne", Origin.OLD_ENGLISH),
    ("burn", Origin.OLD_ENGLISH),
    ("ington", Origin.OLD_ENGLISH),
    ("ton", Origin.OLD_ENGLISH),
    ("ham", Origin.OLD_ENGLISH),
    ("ford", Origin.OLD_ENGLISH),
    ("field", Origin.OLD_ENGLISH),
    ("worth", Origin.OLD_ENGLISH),
    ("stead", Origin.OLD_ENGLISH),
    ("stow", Origin.OLD_ENGLISH),
    ("hurst", Origin.OLD_ENGLISH),
    ("wick", Origin.OLD_ENGLISH),
    ("wich", Origin.OLD_ENGLISH),
    ("leigh", Origin.OLD_ENGLISH),
    ("ley", Origin.OLD_ENGLISH),
    ("den", Origin.OLD_ENGLISH),
    ("dean", Origin.OLD_ENGLISH),
    ("cot", Origin.OLD_ENGLISH),

    # Celtic / Brittonic -- these endings are less common but diagnostic.
    ("combe", Origin.CELTIC),
    ("coombe", Origin.CELTIC),
]


# Prefix rules, checked in order.
_PREFIX_RULES: list[tuple[str, Origin]] = [
    ("aber", Origin.CELTIC),
    ("inver", Origin.CELTIC),
    ("llan", Origin.CELTIC),
    ("caer", Origin.CELTIC),
    ("pen", Origin.CELTIC),
    ("tre", Origin.CELTIC),
    ("pol", Origin.CELTIC),
    ("porth", Origin.CELTIC),
    ("kil", Origin.CELTIC),
    ("dun", Origin.CELTIC),
    ("beau", Origin.NORMAN),
    ("mont", Origin.NORMAN),
]


# A handful of well-known names that the simple affix rules would misclassify.
_OVERRIDES: dict[str, Origin] = {
    "london": Origin.CELTIC,       # pre-English (Londinium is a Latinisation)
    "lincoln": Origin.ROMAN,       # Lindum Colonia
    "york": Origin.OLD_NORSE,      # Jorvik
    "dover": Origin.CELTIC,        # Brittonic *dubras* ("waters")
    "richmond": Origin.NORMAN,     # Norman "riche mont"
    "beaulieu": Origin.NORMAN,
    "avon": Origin.CELTIC,
    "kent": Origin.CELTIC,
    "thames": Origin.CELTIC,
}


def _normalise(name: str) -> str:
    """Lower-case a name and take its final word for suffix matching."""

    return name.strip().lower()


def classify_origin(name: str) -> Origin:
    """Return the most likely linguistic :class:`Origin` for ``name``.

    The check order is: explicit overrides, then prefix rules, then suffix
    rules. Suffixes are the most productive signal for English names, but a
    strong Celtic/Norman prefix (``aber-``, ``beau-``) takes precedence when
    present.
    """

    if not name:
        return Origin.UNKNOWN

    normalised = _normalise(name)
    last_word = normalised.replace("-", " ").split()[-1] if normalised else ""

    if normalised in _OVERRIDES:
        return _OVERRIDES[normalised]
    if last_word in _OVERRIDES:
        return _OVERRIDES[last_word]

    for prefix, origin in _PREFIX_RULES:
        if normalised.startswith(prefix) or last_word.startswith(prefix):
            return origin

    for suffix, origin in _SUFFIX_RULES:
        if last_word.endswith(suffix):
            return origin

    return Origin.UNKNOWN


def color_hex(origin: Origin) -> str:
    """Return the ``#rrggbb`` hex colour for an origin (handy for Plotly)."""

    r, g, b = ORIGIN_COLORS[origin]
    return f"#{r:02x}{g:02x}{b:02x}"
