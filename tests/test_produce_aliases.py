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


def test_pipeline_rebuilds_stale_aliases_when_elements_are_regenerated(
    tmp_path, monkeypatch
):
    import main

    monkeypatch.chdir(tmp_path)
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)
    old_aliases = processed / "aliases.csv"
    old_aliases.write_text(
        "element,alias,alias_type,rule\nstale,stale,original,identity\n",
        encoding="utf-8",
    )

    answers = iter(["n", "n"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(
        main, "process_kepn_data",
        lambda **_kwargs: (
            pd.DataFrame({"PlaceName": ["Ham"], "Derivation": ["ham Old English"]}),
            pd.DataFrame({"Element": ["ham"]}),
        ),
    )
    monkeypatch.setattr(
        main, "save_combined_data", lambda **_kwargs: pd.DataFrame({"NAME": ["Ham"]})
    )
    monkeypatch.setattr(
        main, "convert_to_geo_dataframe", lambda data: data
    )
    monkeypatch.setattr(
        main, "parse_place_names", lambda geo_df, _elements, _truth: geo_df
    )

    main.import_and_process_data()

    actual = pd.read_csv(old_aliases)
    assert actual["element"].tolist() == ["ham"]
    assert actual["alias"].tolist() == ["ham"]
