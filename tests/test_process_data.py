import constants.constants as constants
from pathlib import Path
import pandas as pd

from data_processing.process_csvs import combine_csvs_to_dataframe
from data_processing.process_excel import process_excel_file


def test_combine_csvs_to_dataframe_uses_header_and_concatenates_rows():
    df = combine_csvs_to_dataframe(
        csv_folder=Path("data/raw/opname_csv_gb/Data"),
        header_file=Path("data/raw/opname_csv_gb/Doc/OS_Open_Names_Header.csv"),
        ignored_columns= constants.OS_IGNORED_COLUMNS
    )

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert list(df.columns)[:3] == ["NAME1","NAME2","TYPE"]
    assert len(df.columns) == 13


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
    assert "TOWN_2011NAME" in result.columns
