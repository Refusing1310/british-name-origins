import constants.constants as constants
from pathlib import Path
import pandas as pd
import geopandas as gpd

from data_processing.process_csvs import combine_csvs_to_dataframe, parse_elements
from data_processing.process_excel import process_excel_file


def test_combine_csvs_to_dataframe_uses_header_and_concatenates_rows():
    df = combine_csvs_to_dataframe(
        csv_folder=Path("data/raw/opname_csv_gb/Data"),
        separate_header_file=True,
        header_file=Path("data/raw/opname_csv_gb/Doc/OS_Open_Names_Header.csv"),
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
    assert list(result.columns) == ["Id", "Element", "Language", "Meaning", "Frequency"]
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
    personal_row = result.loc[result["Element"] == "B(i)eda"].iloc[0]

    assert byden_row["Meaning"] == "A vessel, a tub, a butt; used topographically of a hollow."
    assert byden_row["Frequency"] == 1
    assert ford_row["Meaning"] == "A ford."
    assert ford_row["Frequency"] == 1
    assert personal_row["Language"] == "Old English"
    assert personal_row["Meaning"] == "Personal name"


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

    obscure_row = result.loc[result["Element"] == "*Brente"].iloc[0]

    assert obscure_row["Language"] == "Unknown"
    assert obscure_row["Meaning"] == "Obscure element"