"""Starter-review evidence must identify duplicate names without guessing roots."""
import pandas as pd

from data_processing.audit_starters import audit_starters


def test_audit_preserves_source_rows_and_fragments_for_homonymous_entries():
    rows = pd.DataFrame([
        {"PlaceName": "Hall", "Derivation": "tūn Old English - A settlement; Hall D"},
        {"PlaceName": "Hill", "Derivation": "hall Old English - A slope"},
        {"PlaceName": "Hill", "Derivation": "hall Old English - A hill"},
        {"PlaceName": "Other", "Derivation": "tūn Old English - A farm; hall something"},
    ])
    result = audit_starters(rows, {"hall"})
    assert len(result) == 1
    candidate = result[0]
    assert candidate["occurrences"] == 2
    assert candidate["untagged_fragments"] == 2
    assert candidate["places"] == ["Hill"]
    assert candidate["examples"] == [
        {"combined_row_index": 1, "place_name": "Hill",
         "source_fragment": "hall Old English - A slope"},
        {"combined_row_index": 2, "place_name": "Hill",
         "source_fragment": "hall Old English - A hill"},
    ]


def test_audit_evidence_is_bounded_and_deterministic():
    rows = pd.DataFrame([
        {"PlaceName": f"Example {i}", "Derivation": "an C"}
        for i in range(8)
    ])
    first = audit_starters(rows, {"an"})
    assert first == audit_starters(rows, {"an"})
    assert first[0]["occurrences"] == 8
    assert len(first[0]["examples"]) == 5
    assert [x["combined_row_index"] for x in first[0]["examples"]] == list(range(5))
    assert first[0]["untagged_fragments"] == 0
