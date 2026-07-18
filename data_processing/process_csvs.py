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
    
    cleaned_df = clean_dataframe(combined_df, ignored_columns)

    cleaned_df.to_csv(output_path, index=False)
    return cleaned_df


def clean_dataframe(df: pd.DataFrame, ignored_columns: list[str]) -> pd.DataFrame:
    """Clean the dataframe by dropping ignored columns and removing URL prefixes."""
    # Drop ignored columns
    df = df.drop(columns=[col for col in ignored_columns if col in df.columns], errors='ignore')

    # Strip "http://data.ordnancesurvey.co.uk/ontology/admingeo/" from "LOCAL_TYPE" 
    if "LOCAL_TYPE" in df.columns:
        df["LOCAL_TYPE"] = df["LOCAL_TYPE"].str.replace(r'^http://data.ordnancesurvey.co.uk/ontology/admingeo/', '', regex=True)

    # Set any "http://data.ordnancesurvey.co.uk/id/" fields to empty strings in the "TYPE" column
    if "TYPE" in df.columns:
        df["TYPE"] = df["TYPE"].apply(lambda x: "" if isinstance(x, str) and x.startswith("http://data.ordnancesurvey.co.uk/id/") else x)
    
    # Drop any rows where the type is not "populatedPlace"
    # if "TYPE" in combined_df.columns:
    #     combined_df = combined_df[combined_df["TYPE"] == "populatedPlace"]

    return df

