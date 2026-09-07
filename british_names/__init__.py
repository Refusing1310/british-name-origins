"""British place-name origin mapping toolkit.

Modules:
    origins  -- classify a place name by the linguistic origin of its
                prefixes/suffixes (Old English, Old Norse, Celtic, etc.)
    data     -- a curated sample dataset of British towns and cities with
                coordinates and populations, used to demonstrate the map.
"""

from british_names.origins import ORIGIN_COLORS, Origin, classify_origin

__all__ = ["classify_origin", "Origin", "ORIGIN_COLORS"]
