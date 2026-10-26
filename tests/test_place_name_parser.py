"""Candidate discovery must not silently assign etymology or linguistic origin."""
import json

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from data_processing.produce_aliases import build_aliases_csv
from etymology.place_name_parser import find_elements, parse_place_names


def _data(tmp_path):
    elements = pd.DataFrame({
        "Id": [1, 2, 3, 4, 5],
        "Element": ["ham", "ham", "tūn", "an", "eccles"],
        "Language": ["Old English", "Old Norse", "Old English", "C", "Celtic"],
    })
    aliases_file = tmp_path / "aliases.csv"
    build_aliases_csv(elements, aliases_file)
    return elements, aliases_file


def _geo(names):
    return gpd.GeoDataFrame(
        {"NAME": names, "VALUE": list(range(len(names)))},
        geometry=[Point(i, 1) for i in range(len(names))], crs="EPSG:27700",
    )


def test_matches_compound_suffixes_and_preserves_evidence_without_origin_assignment(tmp_path):
    elements, aliases_file = _data(tmp_path)
    geo = _geo(["Birmingham", "Eccles", "An", "Granary", None, ""])
    ground_truth = pd.DataFrame({"PlaceName": ["Birmingham", "Birmingham", "Eccles"]})
    result = parse_place_names(geo, elements, ground_truth, aliases_file=aliases_file)

    ham = json.loads(result.iloc[0]["ElementCandidates"])
    assert len(ham) == 1
    assert ham[0] == {
        "element": "ham", "matched_alias": "ham", "start": 7, "end": 10,
        "position": "suffix", "language_options": ["Old English", "Old Norse"],
        "source_ids": [1, 2],
    }
    assert result.iloc[0]["KEPNNameMatches"] == 2
    assert result.iloc[0]["ElementMatchStatus"] == "unverified_candidates"
    eccles = json.loads(result.iloc[1]["ElementCandidates"])
    assert eccles[0]["language_options"] == ["Celtic"]
    assert json.loads(result.iloc[2]["ElementCandidates"])[0]["language_options"] == ["C"]
    assert result.iloc[3]["ElementCandidateCount"] == 0  # no embedded 'an'
    assert result.iloc[4]["ElementMatchStatus"] == "missing_name"
    assert result.iloc[5]["ElementMatchStatus"] == "missing_name"
    assert result.crs == geo.crs
    assert list(result.geometry) == list(geo.geometry)
    assert result["VALUE"].tolist() == geo["VALUE"].tolist()
    assert "Language" not in result.columns  # no invented place-level origin


def test_overlapping_aliases_preserve_ambiguous_hypotheses(tmp_path):
    elements = pd.DataFrame({"Element": ["ash", "ashdown", "down"],
                             "Language": ["Old English", "Unknown", "Old English"]})
    path = tmp_path / "aliases.csv"
    build_aliases_csv(elements, path)
    result = parse_place_names(_geo(["Ashdown"]), elements, pd.DataFrame(), aliases_file=path)
    candidates = json.loads(result.iloc[0]["ElementCandidates"])
    assert [(m["element"], m["start"], m["end"]) for m in candidates] == [
        ("ashdown", 0, 7), ("ash", 0, 3), ("down", 3, 7)
    ]
    assert result.iloc[0]["KEPNNameMatches"] == 0


def test_casefold_unicode_and_standalone_two_letter_rule(tmp_path):
    elements = pd.DataFrame({"Element": ["Fōrd", "an", "sse"]})
    path = tmp_path / "aliases.csv"
    build_aliases_csv(elements, path)
    assert "fōrd" in find_elements("fōrd", path)
    assert "fōrd" in find_elements("Fo\u0304rd", path)
    assert find_elements("Canterbury", path) == []
    assert "an" in find_elements("AN", path)
    assert "sse" in find_elements("Straße", path)  # casefold-expanded 'ß' -> 'ss'


def test_invalid_or_stale_alias_input_fails_closed(tmp_path):
    elements, path = _data(tmp_path)
    bad = pd.DataFrame({"element": ["invented"], "alias": ["ham"]})
    bad.to_csv(path, index=False)
    with pytest.raises(ValueError, match="unknown source element"):
        parse_place_names(_geo(["Ham"]), elements, pd.DataFrame(), aliases_file=path)
    pd.DataFrame({"wrong": ["ham"]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Alias data requires"):
        parse_place_names(_geo(["Ham"]), elements, pd.DataFrame(), aliases_file=path)


def test_no_duplicates_from_original_and_normalized_aliases(tmp_path):
    elements = pd.DataFrame({"Element": ["Ham", "ham"]})
    path = tmp_path / "aliases.csv"
    build_aliases_csv(elements, path)
    result = parse_place_names(_geo(["Ham"]), elements, pd.DataFrame(), aliases_file=path)
    matches = json.loads(result.iloc[0]["ElementCandidates"])
    assert sorted(m["element"] for m in matches) == ["Ham", "ham"]
    assert result.iloc[0]["ElementCandidateCount"] == 2
