import constants.constants as constants
from pathlib import Path
import pandas as pd
import geopandas as gpd
import pytest

from data_processing.process_csvs import combine_csvs_to_dataframe, get_language_from_derivation, parse_elements
from data_processing.process_excel import process_excel_file


@pytest.fixture
def isolated_parser_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    (processed_dir / "non_definition_starters.csv").write_text("")


def test_combine_csvs_to_dataframe_uses_header_and_concatenates_rows():
    df = combine_csvs_to_dataframe(
        csv_folder=Path(__file__).resolve().parent / "data" / "raw" / "opname_csv_gb" / "Data",
        separate_header_file=True,
        header_file=Path(__file__).resolve().parent / "data" / "raw" / "opname_csv_gb" / "Doc" / "OS_Open_Names_Header.csv",
        ignored_columns= constants.OS_IGNORED_COLUMNS
    )

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert list(df.columns)[:3] == ["ID","NAMES_URI", "NAME1"]
    assert len(df.columns) == 34


def test_process_excel_file_drops_year_columns_when_ignored_columns_are_strings(tmp_path):
    excel_path = tmp_path / "sample.xlsx"
    csv_path = tmp_path / "processed.csv"

    towns_df = pd.DataFrame(
        {
            "TOWN_2011CODE": [1],
            "TOWN_2011NAME": ["Example Town"],
            "AGE GROUP": ["TOTAL"],
            2001: [100],
            2002: [110],
            2018: [180],
            "Population Growth 2001-2019 (%)": [1.2],
        }
    )
    cities_df = pd.DataFrame(
        {
            "TOWN_2011CODE": [2],
            "TOWN_2011NAME": ["Example City"],
            "AGE GROUP": ["TOTAL"],
            2001: [200],
            2002: [220],
            2018: [260],
            "Population Growth 2001-2019 (%)": [2.3],
        }
    )

    with pd.ExcelWriter(excel_path) as writer:
        towns_df.to_excel(writer, sheet_name="Towns (5,000 to 225,000)", index=False)
        cities_df.to_excel(writer, sheet_name="Cities (>225,000) and London", index=False)

    process_excel_file(
        excel_file_path=excel_path,
        ignored_columns=["TOWN_2011CODE", "2001", "2002", "2018", "Population Growth 2001-2019 (%)"],
        csv_file_path=csv_path,
    )

    result = pd.read_csv(csv_path)

    assert "TOWN_2011CODE" not in result.columns
    assert "2001" not in result.columns
    assert "2002" not in result.columns
    assert "2018" not in result.columns
    assert "Population Growth 2001-2019 (%)" not in result.columns
    assert "TOWN NAME" in result.columns
    assert "Population" in result.columns

def test_parse_elements_extracts_meaning_from_derivation_and_counts_frequency():
    df = pd.DataFrame(data=[
        {
            "PlaceName": ["Acol"],
            "Etymology": ["Oak wood"],
            "Derivation": [
                "āc Old English - An oak-tree.; holt Old English - A wood. (Probably of a single species.)",
            ],
        },
        {
            "PlaceName": ["Acrise"],
            "Etymology": ["Oak brushwood"],
            "Derivation": [
                "āc Old English - An oak-tree.; hrīs Old English - Shrubs, brushwood."
            ]
        }]
    )

    result = parse_elements(df)
    acol_row = result.loc[result["Element"] == "āc"].iloc[0]
    holt_row = result.loc[result["Element"] == "holt"].iloc[0]
    hris_row = result.loc[result["Element"] == "hrīs"].iloc[0]
    print(result)
    assert list(result.columns) == ["Id", "Element", "Language", "Meaning", "Frequency", "Reconstructed"]
    assert acol_row["Language"] == "Old English"
    assert acol_row["Meaning"] == "An oak-tree."
    assert acol_row["Frequency"] == 2
    assert holt_row["Language"] == "Old English"
    assert holt_row["Meaning"] == "A wood. (Probably of a single species.)"
    assert holt_row["Frequency"] == 1
    assert hris_row["Language"] == "Old English"
    assert hris_row["Meaning"] == "Shrubs, brushwood."
    assert hris_row["Frequency"] == 1


def test_parse_elements_preserves_semicolons_inside_meanings_and_still_splits_entries():
    df = pd.DataFrame(
        [
            {
                "PlaceName": "Bedford",
                "Etymology": "Uncertain. 'B(i)eda's ford' or perhaps, 'hollow ford'.",
                "Derivation": "byden Old English - A vessel, a tub, a butt; used topographically of a hollow.; ford Old English - A ford.; Personal name (Old English) Old English - Personal name",
            }
        ]
    )

    result = parse_elements(df)

    byden_row = result.loc[result["Element"] == "byden"].iloc[0]
    ford_row = result.loc[result["Element"] == "ford"].iloc[0]

    assert byden_row["Meaning"] == "A vessel, a tub, a butt; used topographically of a hollow."
    assert byden_row["Frequency"] == 1
    assert ford_row["Meaning"] == "A ford."
    assert ford_row["Frequency"] == 1


def test_parse_elements_uses_etymology_clues_for_obscure_elements():
    df = pd.DataFrame(
        [
            {
                "PlaceName": "Brampford Speke",
                "Etymology": "Apparently 'broom ford'. However, evidence shows that the first element was *Brente, an element of obscure origins and meaning. It was held by Richard de Espec ca. 1170.",
                "Derivation": "Family name Unknown - Family name.; ford Old English - A ford.; Obscure element Unknown - Obscure element",
            }
        ]
    )

    result = parse_elements(df)
    print(result)
    obscure_row = result.loc[result["Element"] == "brente"].iloc[0]

    assert obscure_row["Language"] == "Unknown"
    assert obscure_row["Meaning"] == "Obscure element"
    assert bool(obscure_row["Reconstructed"]) is True


def test_parse_elements_merges_identical_rows_even_after_a_different_same_name_entry(isolated_parser_env):
    df = pd.DataFrame(
        [
            {
                "PlaceName": "Dunn Example 1",
                "Etymology": "",
                "Derivation": "dunn Old English - Dun, dull brown.",
            },
            {
                "PlaceName": "Dunn Example 2",
                "Etymology": "",
                "Derivation": "mōr Old English - A marsh, barren upland.",
            },
            {
                "PlaceName": "Dunn Example 3",
                "Etymology": "",
                "Derivation": "mōr Old English - A marsh, barren upland.",
            },
        ]
    )

    result = parse_elements(df)

    dun_rows = result.loc[result["Element"] == "dunn"].sort_values(by=["Meaning"]).reset_index(drop=True)
    mor_rows = result.loc[result["Element"] == "mōr"].sort_values(by=["Meaning"]).reset_index(drop=True)

    assert len(dun_rows) == 1
    assert dun_rows.iloc[0]["Frequency"] == 1
    assert len(mor_rows) == 1
    assert mor_rows.iloc[0]["Frequency"] == 2


def test_parse_elements_keeps_current_derivation_when_a_later_fragment_is_special_case(isolated_parser_env):
    df = pd.DataFrame(
        [
            {
                "PlaceName": "Corscombe",
                "Etymology": "Uncertain. The second element is 'valley'.",
                "Derivation": (
                    'corf Old English - A cutting, a pass, a valley.; '
                    'cumb Old English - A coomb, a valley. Possibly derived from Welsh "cumm"; '
                    'but possibly derived from OE "cumb" a vessel, cup, a small measure.; '
                    'River-name Unknown - River-name; weg Old English - A road.'
                ),
            }
        ]
    )

    result = parse_elements(df)

    corf_row = result.loc[result["Element"] == "corf"].iloc[0]
    cumb_row = result.loc[result["Element"] == "cumb"].iloc[0]
    weg_row = result.loc[result["Element"] == "weg"].iloc[0]

    assert corf_row["Meaning"] == "A cutting, a pass, a valley."
    assert corf_row["Frequency"] == 1
    assert cumb_row["Meaning"] == (
        'A coomb, a valley. Possibly derived from Welsh "cumm; '
        'but possibly derived from OE "cumb" a vessel, cup, a small measure.'
    )
    assert cumb_row["Language"] == "Old English"
    assert weg_row["Meaning"] == "A road."
    assert weg_row["Frequency"] == 1

def test_obscure_element_without_attested_name_falls_back_to_place(isolated_parser_env):
    df = pd.DataFrame(
        [{"PlaceName": "Testham", "Etymology": "Origin unclear.",
          "Derivation": "Obscure element Unknown - Obscure element"}]
    )
    result = parse_elements(df)
    row = result.loc[result["Element"] == "testham"].iloc[0]
    assert row["Language"] == "Unknown"
    assert row["Meaning"] == "Obscure element"
    assert bool(row["Reconstructed"]) is False


@pytest.mark.parametrize(
    "place_name,derivation,element,language,meaning",
    [
        (
            "Sisland",
            "land Old English - Land (as part of earth's surface).",
            "land",
            "Old English",
            "Land (as part of earth's surface).",
        ),
        ("Waterperry", "water Middle English - water", "water", "Middle English", "water"),
        ("Shottermill", "mill Modern English - A mill.", "mill", "Modern English", "A mill."),
    ],
)
def test_language_tagged_special_words_remain_elements(
    isolated_parser_env, place_name, derivation, element, language, meaning
):
    result = parse_elements(
        pd.DataFrame([{"PlaceName": place_name, "Etymology": "", "Derivation": derivation}])
    )

    record = result.loc[result["Element"] == element].iloc[0]
    assert record["Language"] == language
    assert record["Meaning"] == meaning
    assert record["Frequency"] == 1
    assert place_name.lower() not in result["Element"].tolist()


def test_untagged_land_water_mill_keep_original_fallback(isolated_parser_env):
    for place_name, fragment in [
        ("Land Sample", "land"),
        ("Water Sample", "water"),
        ("Mill Sample", "mill"),
    ]:
        result = parse_elements(
            pd.DataFrame([{"PlaceName": place_name, "Etymology": "", "Derivation": fragment}])
        )
        assert result.iloc[0]["Element"] == place_name.lower()


def test_real_kepn_land_water_mill_survive_parsing(isolated_parser_env):
    kepn_dir = Path(__file__).resolve().parents[1] / "data" / "raw" / "kepn"
    df = combine_csvs_to_dataframe(kepn_dir, separate_header_file=False, ignored_columns=[])
    names = {"Sisland", "Waterperry", "Shottermill"}
    examples = df[df["PlaceName"].isin(names)]
    assert set(examples["PlaceName"]) == names

    result = parse_elements(examples)
    for element, language in [
        ("land", "Old English"),
        ("water", "Middle English"),
        ("mill", "Modern English"),
    ]:
        assert not result[(result["Element"] == element) & (result["Language"] == language)].empty


def test_language_tagged_starter_collision_does_not_drop_hall(isolated_parser_env):
    # An unrecognized "Hall D" introduces a continuation marker, but a later
    # tagged hall root is still a real Old English element.
    rows = pd.DataFrame(
        [
            {"PlaceName": "Starter", "Etymology": "", "Derivation":
                "tūn Old English - An enclosure; Hall D"},
            {"PlaceName": "Hall Example", "Etymology": "", "Derivation":
                "hall Old English - A slope, a hill."},
        ]
    )
    result = parse_elements(rows)
    hall = result[(result["Element"] == "hall") & (result["Language"] == "Old English")]
    assert not hall.empty
    assert "A slope, a hill." in hall["Meaning"].tolist()


def test_bundled_kepn_recognizes_tagged_starters(isolated_parser_env):
    # Simulate a persisted continuation cache from an earlier full run.
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("data/processed/non_derivation_starters.csv").write_text("in,an,hall,le\\n")

    kepn = Path(__file__).resolve().parents[1] / "data" / "raw" / "kepn"
    rows = combine_csvs_to_dataframe(kepn, separate_header_file=False, ignored_columns=[])
    examples = rows[rows["PlaceName"].isin(["Landbeach", "Treneglos"])]
    assert set(examples["PlaceName"]) == {"Landbeach", "Treneglos"}

    result = parse_elements(examples)
    for element, lang in [("in", "Old English"), ("an", "C")]:
        assert not result[(result["Element"] == element) & (result["Language"] == lang)].empty


# Issue #15: whole-token KEPN "C" versus capitalized place-name fragments.
@pytest.mark.parametrize(
    "fragment,expected",
    [
        ("Caundle", None),
        ("Coton", None),
        ("Canford", None),
        ("Church", None),
        ("eclẹ̄si̥ā Celtic", "Celtic"),
        ("an C", "C"),
        ("lann C", "C"),
        ("ros C", "C"),
        ("an (C)", "C"),
        ("tūn Old English - an enclosure", "Old English"),
    ],
)
def test_kepn_language_code_c_is_a_whole_token(fragment, expected):
    languages = ["Old English", "Celtic", "C"]
    assert get_language_from_derivation(fragment, languages) == expected


@pytest.mark.parametrize("name,fragment,element", [
    ("Bishop's Caundle", "Caundle", "caundle"),
    ("Coton End", "Coton", "coton"),
    ("Canford Park", "Canford", "canford"),
])
def test_place_name_fragments_do_not_get_c_language(
    isolated_parser_env, name, fragment, element
):
    rows = pd.DataFrame([{"PlaceName": name, "Etymology": "", "Derivation": fragment}])
    result = parse_elements(rows)
    record = result.loc[result["Element"] == element].iloc[0]
    assert pd.isna(record["Language"])


def test_c_language_and_celtic_label_remain_distinct(isolated_parser_env):
    # Preserve a standalone KEPN code while explicitly retaining the supplied
    # "Celtic" label rather than silently dropping these existing source rows.
    rows = pd.DataFrame([
        {"PlaceName": "Example C", "Etymology": "", "Derivation": "an C"},
        {"PlaceName": "Example Celtic", "Etymology": "", "Derivation": "eclẹ̄si̥ā Celtic"},
    ])
    result = parse_elements(rows)
    assert result.loc[result["Element"] == "an"].iloc[0]["Language"] == "C"
    assert result.loc[result["Element"] == "eclẹ̄si̥ā"].iloc[0]["Language"] == "Celtic"
