from pathlib import Path
import pandas as pd


# Process and clean the data from the csv files and save it to a new csv file
# in the data/processed directory.

def load_header_columns(header_file: Path, ignored_columns: list[str] | None = None) -> list[str]:
    """Read the header row from the supplied header CSV file."""
    header_df = pd.read_csv(header_file, header=None)
    if header_df.empty:
        raise ValueError(f"Header file is empty: {header_file}")
    columns = header_df.iloc[0].tolist()
    if ignored_columns:
        columns = [col for col in columns if col not in ignored_columns]
    return columns


def combine_csvs_to_dataframe(
    csv_folder: Path,
    header_file: Path,
    ignored_columns: list[str],
) -> pd.DataFrame:
    """Combine all CSV files in the provided folder into a single dataframe."""
    project_root = Path(__file__).resolve().parents[1]


    columns = load_header_columns(header_file, ignored_columns)
    csv_files = sorted(csv_folder.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {csv_folder}")

    frames = [pd.read_csv(path, header=None, names=columns, dtype=str) for path in csv_files]
    return pd.concat(frames, ignore_index=True)


def save_combined_data(output_path: Path, csv_folder: Path, header_file: Path, ignored_columns: list[str]) -> pd.DataFrame:
    """Create the combined dataframe of data and write it to disk."""

    combined_df = combine_csvs_to_dataframe(csv_folder, header_file, ignored_columns)
    # Drop any rows where the type is not "populatedPlace"
    if "TYPE" in combined_df.columns:
        combined_df = combined_df[combined_df["POPULATED_PLACE_TYPE"] == "populatedPlace"]

    combined_df.to_csv(output_path, index=False)
    return combined_df

