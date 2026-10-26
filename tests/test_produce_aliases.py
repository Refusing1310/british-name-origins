from pathlib import Path

import pandas as pd
import pytest

from data_processing.produce_aliases import ALIAS_COLUMNS, build_aliases_csv


def test_alias_writer_preserves_source_spelling_and_provenance(tmp_path):
    output = tmp_path / "nested" / "aliases.csv"
    elements = pd.DataFrame({
        "Element": ["tūn", "tūn", "Fōrd", "fo\u0304rd", "", None, "   "],
        "Language": ["Old English", "Old Norse", None, None, None, None, None],
    })

    aliases = build_aliases_csv(elements, output)

    assert output.is_file()
    assert aliases.columns.tolist() == ALIAS_COLUMNS
    assert len(aliases) == 5
    assert not {"weight", "confidence", "language"}.intersection(aliases.columns)
    rows = {
        (row.element, row.alias, row.alias_type, row.rule)
        for row in aliases.itertuples(index=False)
    }
    assert ("tūn", "tūn", "original", "identity") in rows
    assert ("Fōrd", "Fōrd", "original", "identity") in rows
    assert ("Fōrd", "fōrd", "normalized", "unicode_nfc_casefold") in rows
    assert ("fo\u0304rd", "fo\u0304rd", "original", "identity") in rows
    assert ("fo\u0304rd", "fōrd", "normalized", "unicode_nfc_casefold") in rows
    pd.testing.assert_frame_equal(pd.read_csv(output), aliases)


def test_alias_writer_is_reproducible_for_identical_input(tmp_path):
    elements = pd.DataFrame({"Element": ["ham", "ham", "Æsc", "ham", None]})
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"

    build_aliases_csv(elements, first)
    build_aliases_csv(elements, second)

    assert first.read_bytes() == second.read_bytes()
    assert pd.read_csv(first)["element"].tolist().count("ham") == 1


def test_empty_elements_produce_header_only_csv(tmp_path):
    path = tmp_path / "aliases.csv"
    result = build_aliases_csv(pd.DataFrame({"Element": [None, "", " "]}), path)
    assert result.empty
    assert list(result.columns) == ALIAS_COLUMNS
    assert list(pd.read_csv(path).columns) == ALIAS_COLUMNS


def test_missing_element_column_is_rejected_without_creating_output(tmp_path):
    path = tmp_path / "aliases.csv"
    with pytest.raises(ValueError, match="Element"):
        build_aliases_csv(pd.DataFrame({"Meaning": ["A hill"]}), path)
    assert not path.exists()
