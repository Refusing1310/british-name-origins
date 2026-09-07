"""Tests for the place-name origin classifier and sample dataset."""

from british_names.data import load_towns
from british_names.origins import Origin, classify_origin


def test_old_norse_suffixes():
    assert classify_origin("Grimsby") is Origin.OLD_NORSE
    assert classify_origin("Scunthorpe") is Origin.OLD_NORSE
    assert classify_origin("Whitby") is Origin.OLD_NORSE


def test_old_english_suffixes():
    assert classify_origin("Northampton") is Origin.OLD_ENGLISH
    assert classify_origin("Birmingham") is Origin.OLD_ENGLISH
    assert classify_origin("Salisbury") is Origin.OLD_ENGLISH
    assert classify_origin("Oxford") is Origin.OLD_ENGLISH


def test_roman_suffixes():
    assert classify_origin("Manchester") is Origin.ROMAN
    assert classify_origin("Doncaster") is Origin.ROMAN
    assert classify_origin("Cirencester") is Origin.ROMAN


def test_celtic_prefixes_and_overrides():
    assert classify_origin("Aberdeen") is Origin.CELTIC
    assert classify_origin("Penzance") is Origin.CELTIC
    assert classify_origin("Inverness") is Origin.CELTIC
    assert classify_origin("London") is Origin.CELTIC


def test_norman():
    assert classify_origin("Beaulieu") is Origin.NORMAN
    assert classify_origin("Richmond") is Origin.NORMAN


def test_empty_is_unknown():
    assert classify_origin("") is Origin.UNKNOWN


def test_sample_dataset_loads_and_is_classified():
    df = load_towns()
    assert len(df) > 40
    assert {"name", "lat", "lon", "population", "origin", "color"}.issubset(df.columns)
    # Every row should get a non-empty origin label.
    assert df["origin"].notna().all()
    # The curated sample should exercise several origins.
    assert df["origin"].nunique() >= 4
