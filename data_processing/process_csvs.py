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
    separate_header_file: bool,
    ignored_columns: list[str],
    header_file: Path | None = None
) -> pd.DataFrame:
    """Combine all CSV files in the provided folder into a single dataframe."""
    if separate_header_file:
        if header_file is None:
            raise ValueError("Header file must be provided when separate_header_file is True.")
        columns = load_header_columns(header_file, ignored_columns)
    else:
        columns = None  # Let pandas infer the columns if no separate header file is provided
    csv_files = sorted(csv_folder.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {csv_folder}")
    
    if columns is None:
        # If no separate header file is provided, read the first CSV to get the columns
        first_csv_df = pd.read_csv(csv_files[0], header=0, dtype=str)
        columns = first_csv_df.columns.tolist()
    frames = [pd.read_csv(path, header=None, names=columns, dtype=str) for path in csv_files]
    return pd.concat(frames, ignore_index=True)


def save_combined_data(output_path: Path, csv_folder: Path, header_file: Path, ignored_columns: list[str]) -> pd.DataFrame:
    """Create the combined dataframe of data and write it to disk."""
    combined_df = combine_csvs_to_dataframe(csv_folder, separate_header_file=True, header_file=header_file, ignored_columns=ignored_columns)
    
    cleaned_df = clean_dataframe(combined_df, ignored_columns)

    cleaned_df.to_csv(output_path, index=False)
    return cleaned_df


def clean_dataframe(df: pd.DataFrame, ignored_columns: list[str]) -> pd.DataFrame:
    """Clean the dataframe by dropping ignored columns and removing URL prefixes, along with ensuring only actual towns and cities are kept."""
    # Drop ignored columns
    df = df.drop(columns=[col for col in ignored_columns if col in df.columns], errors='ignore')

    # Strip "http://data.ordnancesurvey.co.uk/ontology/admingeo/" from "LOCAL_TYPE" 
    if "LOCAL_TYPE" in df.columns:
        df["LOCAL_TYPE"] = df["LOCAL_TYPE"].str.replace(r'^http://data.ordnancesurvey.co.uk/ontology/admingeo/', '', regex=True)

    # Drop any rows where the type is not "populatedPlace"
    if "TYPE" in df.columns:
        df = df[df["TYPE"] == "populatedPlace"]

    # Remove "TYPE" column if it exists
    if "TYPE" in df.columns:
        df = df.drop(columns=["TYPE"])  

    # Rename "NAME1" to "NAME" if it exists
    if "NAME1" in df.columns:
        df = df.rename(columns={"NAME1": "NAME"})
    return df

def process_kepn_data(csv_folder: Path, output_path: Path) -> list[pd.DataFrame]:
    """Read from the CSV folder and save the processed data to a CSV file."""
    ground_truth_df = combine_csvs_to_dataframe(csv_folder, separate_header_file=False, ignored_columns=[])
    elements_df = parse_elements(ground_truth_df.copy())

    return [ground_truth_df, elements_df]
    
def parse_elements(df: pd.DataFrame) -> pd.DataFrame:
    """Parse the elements (roots, suffixes, prefixes) from the kepn dataset"""
    # Create new dataframe to store the elements
    elements_df = pd.DataFrame(columns=["Canonical Name", "Language", "Meaning", "Frequency"])

    # Loop through the dataframe and parse the elements from the "Derivations" column
    if "Derivations" not in df.columns:
        raise ValueError("The 'Derivations' column is missing from the dataframe.")
    return elements_df