"""Read-only audit of cached KEPN continuation starters that also begin real roots.

Run `python -m data_processing.audit_starters` from the repository root.
By default the starter cache is regenerated in a temporary directory; no
tracked source or processed data is modified.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from data_processing.process_csvs import (
    KEPN_LANGUAGES,
    clean_text,
    combine_csvs_to_dataframe,
    get_language_from_derivation,
    parse_elements,
)


def read_starters(path: Path) -> set[str]:
    """The parser persists all starters as a single CSV row, not one per line."""
    if not path.exists():
        raise FileNotFoundError(f"Starter cache does not exist: {path}")
    try:
        raw = pd.read_csv(path, header=None).iloc[0].tolist()
    except pd.errors.EmptyDataError:
        return set()
    return {str(word).strip().lower() for word in raw if pd.notna(word) and str(word).strip()}


def generate_starters(rows: pd.DataFrame) -> set[str]:
    """Generate the parser cache without changing the caller's files."""
    previous_directory = Path.cwd()
    with TemporaryDirectory() as directory:
        try:
            os.chdir(directory)
            cache_path = Path("data/processed/non_derivation_starters.csv")
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            parse_elements(rows)
            return read_starters(cache_path)
        finally:
            os.chdir(previous_directory)


def audit_starters(rows: pd.DataFrame, starters: set[str]) -> list[dict]:
    """Find starter words that appear as language-tagged KEPN derivations.

    A collision is an audit candidate, not a proof that any individual source
    record has been lost; the parser's tagged-root exemption is handled in #10.
    """
    candidates: dict[tuple[str, str], dict] = {}
    for _, row in rows.iterrows():
        derivations = row.get("Derivation")
        if pd.isna(derivations):
            continue
        place = str(row.get("PlaceName") or "")
        for segment in str(derivations).split(";"):
            derivation = clean_text(segment)
            if not derivation:
                continue
            word = derivation.split()[0].strip("()[]\"' ").lower()
            if word not in starters:
                continue
            language = get_language_from_derivation(derivation, KEPN_LANGUAGES)
            if language is None:
                continue
            key = (word, language)
            candidate = candidates.setdefault(key, {
                "starter": word,
                "language": language,
                "occurrences": 0,
                "places": [],
            })
            candidate["occurrences"] += 1
            if place not in candidate["places"] and len(candidate["places"]) < 5:
                candidate["places"].append(place)
    return sorted(candidates.values(), key=lambda x: (-x["occurrences"], x["starter"], x["language"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kepn-dir", type=Path, default=Path("data/raw/kepn"))
    parser.add_argument(
        "--starter-cache", type=Path,
        help="Read an existing parser-generated cache instead of regenerating in a temporary directory",
    )
    args = parser.parse_args()
    rows = combine_csvs_to_dataframe(args.kepn_dir, separate_header_file=False, ignored_columns=[])
    starters = read_starters(args.starter_cache) if args.starter_cache else generate_starters(rows)
    report = {
        "starter_count": len(starters),
        "tagged_collisions": audit_starters(rows, starters),
        "note": "Review these labels against the source; no automatic reclassification is performed.",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
