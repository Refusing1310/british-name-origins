"""Exact OS feature and KEPN source-row review links, never origin inference."""
import pandas as pd
import pytest

from data_processing.place_attestations import (
    LINK_FIELDS, OUTPUT_FIELDS, validate_place_attestations,
)


def example():
    # Fictional places, records and reviewers: no imported name database.
    os_features = pd.DataFrame([
        {"ID": "os-001", "NAME": "Ashford"},
        {"ID": "os-002", "NAME": "Ashford"},
        {"ID": "os-003", "NAME": "North Bay"},
    ])
    kepn = pd.DataFrame([
        {"KEPNSourceFile": "a.csv", "KEPNRecordNumber": 1,
         "PlaceName": "Ashford", "Derivation": "synthetic one"},
        {"KEPNSourceFile": "b.csv", "KEPNRecordNumber": 1,
         "PlaceName": "Ashford", "Derivation": "synthetic alternative"},
        {"KEPNSourceFile": "c.csv", "KEPNRecordNumber": 1,
         "PlaceName": "Bay", "Derivation": "synthetic unrelated substring"},
    ])
    links = pd.DataFrame([
        dict(zip(LINK_FIELDS, ("os-001", "a.csv", 1, "supported_candidate",
                               "synthetic-map-source-a", "fictional-reviewer", False))),
        dict(zip(LINK_FIELDS, ("os-001", "b.csv", 1, "unresolved_candidate",
                               "synthetic-map-source-b", "fictional-reviewer", False))),
        dict(zip(LINK_FIELDS, ("os-002", "b.csv", 1, "rejected_candidate",
                               "synthetic-locality-exclusion", "fictional-reviewer", False))),
    ])
    return os_features, kepn, links


def test_preserves_same_named_localities_source_keys_and_review_decisions():
    os_features, kepn, links = example()
    original_os = os_features.copy(deep=True)
    original_kepn = kepn.copy(deep=True)
    result = validate_place_attestations(os_features, kepn, links)
    assert result.columns.tolist() == list(OUTPUT_FIELDS)
    assert result["OSFeatureId"].tolist() == ["os-001", "os-001", "os-002"]
    assert result["GroundTruthRow"].tolist() == [0, 1, 1]
    assert result["Decision"].tolist() == [
        "supported_candidate", "unresolved_candidate", "rejected_candidate"
    ]
    assert set(result["EvidenceStatus"]) == {
        "review_record_claim_only_not_independently_verified"
    }
    assert result["NameStringsMatch"].tolist() == [True, True, True]
    pd.testing.assert_frame_equal(os_features, original_os)
    pd.testing.assert_frame_equal(kepn, original_kepn)


def test_multiple_supported_rows_are_preserved_and_flagged_not_collapsed():
    os_features, kepn, links = example()
    links.loc[1, "Decision"] = "supported_candidate"
    result = validate_place_attestations(os_features, kepn, links)
    first = result[result["OSFeatureId"] == "os-001"]
    assert first["SupportedAlternatives"].tolist() == [2, 2]
    assert set(first["ConflictStatus"]) == {"multiple_supported_candidates"}


def test_matching_strings_are_not_automatically_attested():
    os_features, kepn, links = example()
    result = validate_place_attestations(os_features, kepn, links.iloc[:0])
    assert result.empty
    assert result.columns.tolist() == list(OUTPUT_FIELDS)


def test_mismatched_name_and_unrelated_substring_need_explicit_review():
    os_features, kepn, links = example()
    links.loc[0] = ["os-003", "c.csv", 1, "supported_candidate",
                    "synthetic-specific-geography-review", "fictional-reviewer", False]
    with pytest.raises(ValueError, match="mismatch review"):
        validate_place_attestations(os_features, kepn, links)
    links.loc[0, "NameMismatchReviewed"] = True
    result = validate_place_attestations(os_features, kepn, links)
    changed = result[result["OSFeatureId"] == "os-003"].iloc[0]
    assert changed["NameStringsMatch"] == False
    assert changed["Decision"] == "supported_candidate"
    assert changed["EvidenceStatus"].startswith("review_record_claim")


@pytest.mark.parametrize("field,value", [
    ("OSFeatureId", "unknown-feature"),
    ("KEPNSourceFile", "nonexistent.csv"),
    ("KEPNRecordNumber", 2),
    ("KEPNRecordNumber", True),
    ("KEPNRecordNumber", "1"),
    ("Decision", "verified"),
    ("EvidenceRef", ""),
    ("ReviewerRef", ""),
    ("NameMismatchReviewed", None),
    ("NameMismatchReviewed", 1),
])
def test_missing_unreviewed_invalid_or_unattributed_links_fail_closed(field, value):
    os_features, kepn, links = example()
    links.at[0, field] = value
    with pytest.raises(ValueError):
        validate_place_attestations(os_features, kepn, links)


def test_duplicate_conflicting_pair_or_source_record_fails_closed():
    os_features, kepn, links = example()
    twice = pd.concat([links, links.iloc[:1]], ignore_index=True)
    twice.loc[len(twice) - 1, "Decision"] = "rejected_candidate"
    with pytest.raises(ValueError, match="Duplicate or contradictory"):
        validate_place_attestations(os_features, kepn, twice)
    with pytest.raises(ValueError, match="Duplicate KEPN"):
        validate_place_attestations(
            os_features, pd.concat([kepn, kepn.iloc[:1]], ignore_index=True), links
        )
    with pytest.raises(ValueError, match="Duplicate OS"):
        validate_place_attestations(
            pd.concat([os_features, os_features.iloc[:1]], ignore_index=True), kepn, links
        )


def test_missing_columns_fail_closed():
    os_features, kepn, links = example()
    with pytest.raises(ValueError, match="missing required"):
        validate_place_attestations(os_features.drop(columns=["ID"]), kepn, links)
