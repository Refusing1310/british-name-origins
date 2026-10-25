from pathlib import Path

import pandas as pd
import pytest

from data_processing.audit_starters import audit_starters, generate_starters, read_starters


def test_read_starters_accepts_single_csv_row(tmp_path):
    file = tmp_path / "starters.csv"
    file.write_text("hall,an,le,,In\\n", encoding="utf-8")
    assert read_starters(file) == {"hall", "an", "le", "in"}


def test_read_starters_empty_cache(tmp_path):
    file = tmp_path / "starters.csv"
    file.write_text("", encoding="utf-8")
    assert read_starters(file) == set()


def test_audit_only_reports_language_tagged_collisions():
    rows = pd.DataFrame([
        {"PlaceName": "Continuation", "Derivation": "Hall D; Canford"},
        {"PlaceName": "Hill", "Derivation": "hall Old English - A hill."},
        {"PlaceName": "Article", "Derivation": "an C"},
        {"PlaceName": "Celtic example", "Derivation": "an Celtic"},
        {"PlaceName": "Plain fragment", "Derivation": "Coton"},
        {"PlaceName": "Unused", "Derivation": None},
    ])
    found = audit_starters(rows, {"hall", "an", "coton", "canford"})
    assert [(v["starter"], v["language"], v["occurrences"]) for v in found] == [
        ("an", "C", 1),
        ("an", "Celtic", 1),
        ("hall", "Old English", 1),
    ]
    assert found[2]["places"] == ["Hill"]


def test_generate_starters_keeps_working_directory_and_writes_only_to_temp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rows = pd.DataFrame([
        {"PlaceName": "Test", "Etymology": "",
         "Derivation": "tūn Old English - An enclosure; Hall D"},
    ])
    assert "hall" in generate_starters(rows)
    assert Path.cwd() == tmp_path
    assert not (tmp_path / "data").exists()
