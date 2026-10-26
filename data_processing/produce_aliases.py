"""Deterministic, auditable aliases for linguistic elements.

Aliases are matching forms, not statements about language, meaning or history.
Only exact source spellings and Unicode-normalized casefolds are generated.
Additional historical/orthographic spellings require curated evidence.
"""
from pathlib import Path
import unicodedata

import pandas as pd


ALIAS_COLUMNS = ["element", "alias", "alias_type", "rule"]


def build_aliases_csv(elements_df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """Write reproducible, provenance-labelled aliases from parsed KEPN elements.

    Preserve each source spelling exactly apart from surrounding whitespace.
    Do not invent phonetic variants, language assignments or match weights.
    Multiple etymologies may share the same spelling; alias deduplication
    does not deduplicate the original element records.
    """
    if "Element" not in elements_df.columns:
        raise ValueError("The 'Element' column is missing from the dataframe.")

    records: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for value in elements_df["Element"]:
        if pd.isna(value):
            continue
        element = str(value).strip()
        if not element:
            continue

        normalized = unicodedata.normalize("NFC", element).casefold()
        variants = [
            (element, "original", "identity"),
            (normalized, "normalized", "unicode_nfc_casefold"),
        ]
        for alias, alias_type, rule in variants:
            if not alias or (element, alias) in seen:
                continue
            seen.add((element, alias))
            records.append({
                "element": element,
                "alias": alias,
                "alias_type": alias_type,
                "rule": rule,
            })

    aliases_df = pd.DataFrame.from_records(records, columns=ALIAS_COLUMNS)
    aliases_df = aliases_df.sort_values(
        ["element", "alias", "alias_type"], kind="stable"
    ).reset_index(drop=True)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    aliases_df.to_csv(output_path, index=False)
    return aliases_df
