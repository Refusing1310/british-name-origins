"""Fail-closed, source-row-specific links to *curated* personal-name records.

This does not scrape external lexicons, infer a personal name from a place-name
gloss, assign a meaning to KEPN's generic 'Personal name' element, or certify
any licensing/linguistic claim. A researcher must curate every entry and link.
"""
from numbers import Integral
import re

import pandas as pd


NAME_FIELDS = (
    "NameId", "Form", "Language", "Meaning",
    "SourceRef", "MeaningRef", "PermissionStatus",
)
LINK_FIELDS = (
    "GroundTruthRow", "ElementId", "OccurrenceInRow",
    "NameId", "EvidenceRef",
)
SOURCE_FIELDS = (
    "GroundTruthRow", "ElementId", "OccurrenceInRow",
    "KEPNSourceFile", "KEPNRecordNumber",
)
OUTPUT_FIELDS = (*LINK_FIELDS, "KEPNSourceFile", "KEPNRecordNumber", "ReviewStatus")
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
_PERMISSIONS = {"pending", "reviewed"}


def _str(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    if not isinstance(value, str):
        raise ValueError("Expected a textual registry field")
    return value.strip()


def _integer(value: object, field: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or int(value) < minimum:
        raise ValueError(f"{field}: expected integer >= {minimum}")
    return int(value)


def _required_columns(frame: pd.DataFrame, names: tuple[str, ...], label: str) -> None:
    if not isinstance(frame, pd.DataFrame) or not set(names).issubset(frame.columns):
        raise ValueError(f"{label}: missing required columns")


def validate_curated_personal_name_links(
    names: pd.DataFrame,
    proposed_links: pd.DataFrame,
    element_sources: pd.DataFrame,
    elements: pd.DataFrame,
) -> pd.DataFrame:
    """Return source-joined *unverified candidate* links or raise on bad input.

    NameId is a local registry ID, not a PASE/DMNES person identifier.
    The original KEPN elements and meanings are never mutated. A generic
    element can occur in many unrelated place names: association must use
    the unique source-row/element/occurrence tuple, not ElementId alone.
    PermissionStatus records a human assertion, never verifies legal rights.
    """
    _required_columns(names, NAME_FIELDS, "names")
    _required_columns(proposed_links, LINK_FIELDS, "proposed_links")
    _required_columns(element_sources, SOURCE_FIELDS, "element_sources")
    _required_columns(elements, ("Id", "Element"), "elements")

    name_ids: set[str] = set()
    for row in names.to_dict("records"):
        ident = _str(row["NameId"])
        if not _ID_RE.fullmatch(ident) or ident in name_ids:
            raise ValueError("NameId must be unique and a stable local identifier")
        name_ids.add(ident)
        if not _str(row["Form"]) or not _str(row["Language"]) or not _str(row["SourceRef"]):
            raise ValueError("Name record requires form, language and attributable source")
        status = _str(row["PermissionStatus"])
        if status not in _PERMISSIONS:
            raise ValueError("PermissionStatus must be pending or reviewed")
        meaning = _str(row["Meaning"])
        meaning_ref = _str(row["MeaningRef"])
        if meaning and (not meaning_ref or status != "reviewed"):
            raise ValueError("Nonempty meaning requires a specific citation and rights review")
        if meaning_ref and not meaning:
            raise ValueError("MeaningRef without meaning is not allowed")

    placeholders: set[int] = set()
    for row in elements.to_dict("records"):
        ident = _integer(row["Id"], "Id")
        label = _str(row["Element"])
        if label.casefold().startswith("personal name"):
            placeholders.add(ident)

    source_keys: dict[tuple[int, int, int], tuple[str, int]] = {}
    for row in element_sources.to_dict("records"):
        key = (
            _integer(row["GroundTruthRow"], "GroundTruthRow"),
            _integer(row["ElementId"], "ElementId"),
            _integer(row["OccurrenceInRow"], "OccurrenceInRow", minimum=1),
        )
        origin = (
            _str(row["KEPNSourceFile"]),
            _integer(row["KEPNRecordNumber"], "KEPNRecordNumber", minimum=1),
        )
        if not origin[0] or key in source_keys:
            raise ValueError("Source occurrence must have unique row and exact KEPN provenance")
        source_keys[key] = origin

    output: list[dict] = []
    seen: set[tuple[int, int, int, str]] = set()
    for row in proposed_links.to_dict("records"):
        key = (
            _integer(row["GroundTruthRow"], "GroundTruthRow"),
            _integer(row["ElementId"], "ElementId"),
            _integer(row["OccurrenceInRow"], "OccurrenceInRow", minimum=1),
        )
        name_id = _str(row["NameId"])
        reference = _str(row["EvidenceRef"])
        if name_id not in name_ids or key not in source_keys:
            raise ValueError("Personal-name link references unknown registry or source occurrence")
        if key[1] not in placeholders:
            raise ValueError("Personal-name link must target a generic personal-name element")
        if not reference:
            raise ValueError("Every candidate link needs a source-specific evidence reference")
        token = (*key, name_id)
        if token in seen:
            raise ValueError("Duplicate name link for the same source occurrence")
        seen.add(token)
        filename, record_number = source_keys[key]
        output.append(dict(zip(
            OUTPUT_FIELDS,
            (*key, name_id, reference, filename, record_number, "unverified_candidate"),
        )))
    return pd.DataFrame(output, columns=OUTPUT_FIELDS).sort_values(
        ["GroundTruthRow", "OccurrenceInRow", "NameId"], kind="stable"
    ).reset_index(drop=True)
