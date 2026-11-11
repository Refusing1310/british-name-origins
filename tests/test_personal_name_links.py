"""Only explicitly curated personal-name links may cross the KEPN boundary."""
import pandas as pd
import pytest

from data_processing.personal_name_links import (
    LINK_FIELDS, NAME_FIELDS, OUTPUT_FIELDS, validate_curated_personal_name_links,
)


def _fixtures():
    names = pd.DataFrame([
        dict(zip(NAME_FIELDS, ("name-abba", "Abba", "Old English", "", 
                               "fictional-source-a", "", "pending"))),
        dict(zip(NAME_FIELDS, ("name-bola", "Bola", "Old English", "",
                               "fictional-source-b", "", "pending"))),
    ])
    sources = pd.DataFrame([
        {"GroundTruthRow": 0, "ElementId": 7, "OccurrenceInRow": 1,
         "KEPNSourceFile": "synthetic.csv", "KEPNRecordNumber": 1},
        {"GroundTruthRow": 1, "ElementId": 7, "OccurrenceInRow": 1,
         "KEPNSourceFile": "synthetic.csv", "KEPNRecordNumber": 2},
        {"GroundTruthRow": 1, "ElementId": 8, "OccurrenceInRow": 2,
         "KEPNSourceFile": "synthetic.csv", "KEPNRecordNumber": 2},
    ])
    elements = pd.DataFrame([
        {"Id": 7, "Element": "Personal name (Old English)", "Meaning": "Personal name"},
        {"Id": 8, "Element": "tūn", "Meaning": "A farmstead"},
    ])
    links = pd.DataFrame([
        dict(zip(LINK_FIELDS, (0, 7, 1, "name-abba", "synthetic row-1 gloss"))),
        dict(zip(LINK_FIELDS, (1, 7, 1, "name-bola", "synthetic row-2 gloss"))),
    ])
    return names, links, sources, elements


def test_curated_links_are_source_specific_and_preserve_placeholder():
    names, links, sources, elements = _fixtures()
    before = elements.copy(deep=True)
    result = validate_curated_personal_name_links(names, links, sources, elements)
    assert result.columns.tolist() == list(OUTPUT_FIELDS)
    assert result["NameId"].tolist() == ["name-abba", "name-bola"]
    assert result["KEPNRecordNumber"].tolist() == [1, 2]
    assert set(result["ReviewStatus"]) == {"unverified_candidate"}
    pd.testing.assert_frame_equal(elements, before)
    assert elements.loc[0, "Meaning"] == "Personal name"


def test_alternative_name_forms_remain_separate_unverified_candidates():
    names, links, sources, elements = _fixtures()
    links.loc[len(links)] = [0, 7, 1, "name-bola", "alternative synthetic hypothesis"]
    result = validate_curated_personal_name_links(names, links, sources, elements)
    assert result[result["GroundTruthRow"] == 0]["NameId"].tolist() == [
        "name-abba", "name-bola"
    ]


@pytest.mark.parametrize("field,value", [
    ("NameId", "unknown"),
    ("EvidenceRef", ""),
    ("ElementId", 8),
    ("GroundTruthRow", 20),
    ("OccurrenceInRow", 4),
])
def test_unknown_or_unattributed_links_fail_closed(field, value):
    names, links, sources, elements = _fixtures()
    links.loc[0, field] = value
    with pytest.raises(ValueError):
        validate_curated_personal_name_links(names, links, sources, elements)


def test_duplicate_links_and_source_occurrences_rejected():
    names, links, sources, elements = _fixtures()
    duplicate = pd.concat([links, links.iloc[:1]], ignore_index=True)
    with pytest.raises(ValueError, match="Duplicate"):
        validate_curated_personal_name_links(names, duplicate, sources, elements)
    with pytest.raises(ValueError, match="unique"):
        validate_curated_personal_name_links(
            names, links, pd.concat([sources, sources.iloc[:1]], ignore_index=True), elements
        )


def test_meaning_requires_attributable_citation_and_review_not_just_a_name():
    names, links, sources, elements = _fixtures()
    names.loc[0, "Meaning"] = "example semantic gloss"
    with pytest.raises(ValueError, match="rights review"):
        validate_curated_personal_name_links(names, links, sources, elements)
    names.loc[0, "MeaningRef"] = "fictional scholarly reference"
    names.loc[0, "PermissionStatus"] = "reviewed"
    validate_curated_personal_name_links(names, links, sources, elements)
    names.loc[0, "NameId"] = "name-bola"
    with pytest.raises(ValueError, match="unique"):
        validate_curated_personal_name_links(names, links, sources, elements)


def test_empty_curated_registry_is_a_valid_nonclaim():
    names, links, sources, elements = _fixtures()
    result = validate_curated_personal_name_links(names.iloc[:0], links.iloc[:0], sources, elements)
    assert result.empty
    assert result.columns.tolist() == list(OUTPUT_FIELDS)
