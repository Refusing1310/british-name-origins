"""Conservative alias-based candidate discovery for British place names.

A substring match is *not* evidence that an etymology or language is correct.
Consumers must keep candidates separate from historically verified derivations.
"""

from collections import Counter, defaultdict
import json
from pathlib import Path
import unicodedata

import geopandas as gpd
import pandas as pd


DEFAULT_ALIASES_FILE = Path("data/processed/aliases.csv")
_TERMINAL = None


def _normalise(value: str) -> str:
    """Use only transformations provided by the alias-generation pipeline."""
    return unicodedata.normalize("NFC", value).casefold()


def _read_aliases(path: Path) -> pd.DataFrame:
    # Do not convert a legitimate literal alias like "NA" to a missing value.
    return pd.read_csv(path, keep_default_na=False)


def _compile_aliases(aliases_df: pd.DataFrame, elements_df: pd.DataFrame) -> dict:
    """Build a trie and retain distinct language/source-record alternatives."""
    if not {"alias", "element"}.issubset(aliases_df.columns):
        raise ValueError("Alias data requires 'alias' and 'element' columns")
    if "Element" not in elements_df.columns:
        raise ValueError("Element data requires an 'Element' column")

    languages: dict[str, set[str]] = defaultdict(set)
    ids: dict[str, set[int]] = defaultdict(set)
    source_records: dict[str, dict[int, dict]] = defaultdict(dict)
    for row in elements_df.itertuples(index=False):
        value = getattr(row, "Element")
        if pd.isna(value) or not str(value).strip():
            continue
        element = str(value).strip()
        languages.setdefault(element, set())
        if "Language" in elements_df.columns:
            lang = getattr(row, "Language")
            if pd.notna(lang) and str(lang).strip():
                languages[element].add(str(lang).strip())
        if "Id" in elements_df.columns:
            source_id = getattr(row, "Id")
            if pd.notna(source_id):
                source_id = int(source_id)
                ids[element].add(source_id)
                language = getattr(row, "Language") if "Language" in elements_df.columns else None
                language = str(language).strip() if pd.notna(language) and str(language).strip() else None
                reconstructed = getattr(row, "Reconstructed") if "Reconstructed" in elements_df.columns else None
                reconstructed = bool(reconstructed) if pd.notna(reconstructed) else None
                record = {
                    "id": source_id,
                    "language": language,
                    "reconstructed": reconstructed,
                }
                if source_id in source_records[element] and source_records[element][source_id] != record:
                    raise ValueError(f"Conflicting element source ID: {source_id}")
                source_records[element][source_id] = record

    trie: dict = {}
    for row in aliases_df.itertuples(index=False):
        element = str(row.element).strip()
        alias = _normalise(str(row.alias).strip())
        if not element or not alias:
            continue
        if element not in languages:
            raise ValueError(f"Alias references unknown source element: {element!r}")
        # Current alias generation permits only exact source spellings and
        # NFC-casefold transforms; an unrelated alias must not silently create
        # a fabricated candidate even if its element name still exists.
        if alias != _normalise(element):
            raise ValueError(f"Alias spelling is not source-preserving: {element!r} -> {alias!r}")
        node = trie
        for character in alias:
            node = node.setdefault(character, {})
        node.setdefault(_TERMINAL, set()).add((alias, element))

    evidence = {
        element: {
            "language_options": sorted(options),
            "source_ids": sorted(ids[element]),
            "source_records": [source_records[element][key] for key in sorted(source_records[element])],
        }
        for element, options in languages.items()
    }
    return {"trie": trie, "evidence": evidence}


def _match(name: str, compiled: dict) -> list[dict]:
    normalized = _normalise(name)
    result: list[dict] = []
    trie = compiled["trie"]
    for start in range(len(normalized)):
        node = trie
        end = start
        while end < len(normalized) and normalized[end] in node:
            node = node[normalized[end]]
            end += 1
            for alias, element in sorted(node.get(_TERMINAL, ())):
                # Single/two-character substrings inside longer names are
                # especially prone to false matches. Retain only whole tokens.
                if len(alias) < 3 and (
                    (start > 0 and normalized[start - 1].isalnum())
                    or (end < len(normalized) and normalized[end].isalnum())
                ):
                    continue
                position = (
                    "whole" if start == 0 and end == len(normalized)
                    else "prefix" if start == 0
                    else "suffix" if end == len(normalized)
                    else "internal"
                )
                result.append({
                    "element": element,
                    "matched_alias": alias,
                    "start": start,
                    "end": end,
                    "position": position,
                    **compiled["evidence"][element],
                })
    # Keep overlapping hypotheses instead of choosing an unsupported winner.
    return sorted(result, key=lambda match: (
        match["start"], -(match["end"] - match["start"]), match["element"]
    ))


def parse_place_names(
    geo_df: gpd.GeoDataFrame,
    elements_df: pd.DataFrame,
    ground_truth_df: pd.DataFrame,
    *,
    aliases_file: Path = DEFAULT_ALIASES_FILE,
) -> gpd.GeoDataFrame:
    """Attach auditable *candidates*, not inferred origins, to OS place names.

    start/end offsets index the NFC-casefolded name (not original
    characters, since casefolding may expand a character). KEPNNameMatches
    counts identical *name strings*, not uniquely identified locations.
    No language in a candidate is an established origin for that place.
    """
    if "NAME" not in geo_df.columns:
        raise ValueError("GeoDataFrame requires a 'NAME' column")

    compiled = _compile_aliases(_read_aliases(Path(aliases_file)), elements_df)
    known = Counter()
    if "PlaceName" in ground_truth_df.columns:
        for value in ground_truth_df["PlaceName"]:
            if pd.notna(value) and str(value).strip():
                known[_normalise(str(value).strip())] += 1

    matches_json = []
    counts = []
    statuses = []
    kepn_counts = []
    for value in geo_df["NAME"]:
        if pd.isna(value) or not str(value).strip():
            matches = []
            status = "missing_name"
            kepn_count = 0
        else:
            name = str(value).strip()
            matches = _match(name, compiled)
            status = "unverified_candidates" if matches else "no_candidates"
            kepn_count = known[_normalise(name)]
        matches_json.append(json.dumps(matches, ensure_ascii=False, separators=(",", ":")))
        counts.append(len(matches))
        statuses.append(status)
        kepn_counts.append(kepn_count)

    result = geo_df.copy()
    result["ElementCandidates"] = matches_json
    result["ElementCandidateCount"] = counts
    result["ElementMatchStatus"] = statuses
    result["KEPNNameMatches"] = kepn_counts
    return result


def find_elements(place_name: str, aliases_file: Path) -> list[str]:
    """Return unique matching aliases (not verified historical elements).

    Convenience interface for a single name; batch matching compiles the
    index once via parse_place_names for substantially better performance.
    """
    aliases_df = _read_aliases(Path(aliases_file))
    if not {"alias", "element"}.issubset(aliases_df.columns):
        raise ValueError("Alias data requires 'alias' and 'element' columns")
    elements_df = pd.DataFrame({"Element": aliases_df["element"].unique()})
    matches = _match(place_name, _compile_aliases(aliases_df, elements_df))
    return list(dict.fromkeys(match["matched_alias"] for match in matches))
