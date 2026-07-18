from pathlib import Path
import pandas as pd

from scripts.process_data import combine_csvs_to_dataframe


def test_combine_csvs_to_dataframe_uses_header_and_concatenates_rows():
    df = combine_csvs_to_dataframe()

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert list(df.columns)[:3] == ["ID", "NAMES_URI", "NAME1"]
    assert len(df.columns) == 33
