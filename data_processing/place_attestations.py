"""Human-recorded OS-to-KEPN associations; never auto-verify place-name origins.

These checks validate identifiers, evidence presence and ambiguity only.
A link record is NOT evidence that a reviewer was qualified, that source
rights permit redistribution, or that an etymology is historically correct.
"""
from __future__ import annotations

from collections import Counter
import unicodedata

import pandas as pd


LINK_FIELDS = (
    "OSFeatureId", "KEPNSourceFile", "KEPNRecordNumber",
    "Decision", "EvidenceRef", "ReviewerRef", "NameMismatchReviewed",
)
DECISIONS = frozenset({"supported_candidate", "rejected_candidate", "unresolved_candidate"})
OUTPUT_FIELDS = (
    *LINK_FIELDS, "OSPlaceName", "KEPNPlaceName", "GroundTruthRow",
    "NameStringsMatch", "SupportedAlternatives", "ConflictStatus", "EvidenceStatus",
)


def _required(frame: pd.DataFrame, fields: tuple[str, ...], name: str) -> None:
    if not isinstance(frame, pd.DataFrame) or not set(fields).issubset(frame.columns):
        raise ValueError(f"{name}: missing required columns")


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}: nonempty string required")
    return value.strip()


def _record_number(value: object) -> int:
    if type(value) is not int or value < 1:
        raise ValueError("KEPNRecordNumber: positive integer required")
    return value


def _normalise(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold()


def validate_place_attestations(
    os_features: pd.DataFrame,
    kepn_rows: pd.DataFrame,
    links: pd.DataFrame,
) -> pd.DataFrame:
    """Validate human-entered link proposals while retaining contrary evidence.

    OS ID identifies a specific OS geographic feature; the KEPN file/record
    pair identifies one original derivation row. Matching place-name strings
    do not themselves establish a source-to-location association. Only
    explicit source-specific evidence records may appear in this output.
    """
    _required(os_features, ("ID", "NAME"), "os_features")
    _required(kepn_rows, ("KEPNSourceFile", "KEPNRecordNumber", "PlaceName"), "kepn_rows")
    _required(links, LINK_FIELDS, "links")

    os_index: dict[str, str] = {}
    for row in os_features.to_dict("records"):
        ident = _text(row["ID"], "OS ID")
        name = _text(row["NAME"], "OS NAME")
        if ident in os_index:
            raise ValueError("Duplicate OS feature identifier")
        os_index[ident] = name

    kepn_index: dict[tuple[str, int], tuple[int, str]] = {}
    for index, row in enumerate(kepn_rows.to_dict("records")):
        origin = (
            _text(row["KEPNSourceFile"], "KEPN source filename"),
            _record_number(row["KEPNRecordNumber"]),
        )
        name = _text(row["PlaceName"], "KEPN place name")
        if origin in kepn_index:
            raise ValueError("Duplicate KEPN source-row identifier")
        kepn_index[origin] = (index, name)

    proposed: list[dict] = []
    seen: set[tuple[str, str, int]] = set()
    for row in links.to_dict("records"):
        ident = _text(row["OSFeatureId"], "OSFeatureId")
        source = _text(row["KEPNSourceFile"], "KEPNSourceFile")
        record = _record_number(row["KEPNRecordNumber"])
        key = (ident, source, record)
        if key in seen:
            raise ValueError("Duplicate or contradictory association for the same source pair")
        seen.add(key)
        if ident not in os_index or (source, record) not in kepn_index:
            raise ValueError("Link references unknown OS feature or KEPN source row")
        decision = _text(row["Decision"], "Decision")
        if decision not in DECISIONS:
            raise ValueError("Invalid explicit candidate decision")
        evidence = _text(row["EvidenceRef"], "EvidenceRef")
        reviewer = _text(row["ReviewerRef"], "ReviewerRef")
        mismatch_reviewed = row["NameMismatchReviewed"]
        if type(mismatch_reviewed) is not bool:
            raise ValueError("NameMismatchReviewed must be an explicit boolean")
        row_idx, kepn_name = kepn_index[(source, record)]
        os_name = os_index[ident]
        matched = _normalise(os_name) == _normalise(kepn_name)
        if not matched and decision == "supported_candidate" and not mismatch_reviewed:
            raise ValueError("A proposed support decision with different names needs explicit mismatch review")
        proposed.append({
            "OSFeatureId": ident,
            "KEPNSourceFile": source,
            "KEPNRecordNumber": record,
            "Decision": decision,
            "EvidenceRef": evidence,
            "ReviewerRef": reviewer,
            "NameMismatchReviewed": mismatch_reviewed,
            "OSPlaceName": os_name,
            "KEPNPlaceName": kepn_name,
            "GroundTruthRow": row_idx,
            "NameStringsMatch": matched,
        })

    positives = Counter(row["OSFeatureId"] for row in proposed
                        if row["Decision"] == "supported_candidate")
    output = []
    for row in proposed:
        alternatives = positives[row["OSFeatureId"]]
        row["SupportedAlternatives"] = alternatives
        row["ConflictStatus"] = ("multiple_supported_candidates"
                                 if alternatives > 1 else "not_independently_resolved")
        row["EvidenceStatus"] = "review_record_claim_only_not_independently_verified"
        output.append(row)
    return pd.DataFrame(output, columns=OUTPUT_FIELDS).sort_values(
        ["OSFeatureId", "KEPNSourceFile", "KEPNRecordNumber"], kind="stable",
    ).reset_index(drop=True)
