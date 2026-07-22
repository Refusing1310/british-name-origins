from pathlib import Path
from typing import TypedDict
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
    if separate_header_file:
        # If a separate header file isn't provided, skip the first row of each CSV file
        frames = [pd.read_csv(path, header=None, names=columns, dtype=str) for path in csv_files]
    else:
        frames = [pd.read_csv(path, header=0, names=columns, dtype=str) for path in csv_files]
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

def process_kepn_data(csv_folder: Path, output_folder: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read from the CSV folder and save the processed data to a CSV file."""
    ground_truth_df = combine_csvs_to_dataframe(csv_folder, separate_header_file=False, ignored_columns=[])
    ground_truth_df.to_csv(output_folder / "ground_truth.csv", index=False)
    elements_df = parse_elements(ground_truth_df.copy())
    elements_df.to_csv(output_folder / "elements.csv", index=False)
    return (ground_truth_df, elements_df)


class ElementRecord(TypedDict):
    """Parsed element data extracted from the derivation text."""
    Id: int
    Element: str
    Language: str | None
    Meaning: str | None
    Frequency: int
    
def parse_elements(df: pd.DataFrame) -> pd.DataFrame:
    """Parse the elements (roots, suffixes, prefixes) from the KEPN dataset."""
    if "Derivation" not in df.columns:
        raise ValueError("The 'Derivation' column is missing from the dataframe.")

    elements: dict[int, ElementRecord] = {}

    for _, row in df.iterrows():
        derivations = row["Derivation"]
        if pd.isna(derivations):
            continue

        for element in str(derivations).split(";"):
            element = clean_text(element)
            if not element:
                continue
            meaning = None
            if " - " not in element:
                language = "Modern English"
                Meaning = element
            else:
                head, meaning = element.split(" - ", 1)
                head = clean_text(head) or ""
                meaning = clean_text(meaning)
                head_parts = head.split()
                element = head_parts[0]
                language = " ".join(head_parts[1:]) if len(head_parts) > 1 else None
            
            existing_record = locateElement(elements, element)
            if existing_record is None:
                id = len(elements) + 1
                elements[id] = {
                    "Id": id,
                    "Element": element,
                    "Language": language,
                    "Meaning": meaning,
                    "Frequency": 1,
                }
            # If element already exists, with a different meaning or language, create a new entry with a unique ID. Otherwise, increment the frequency.
            elif existing_record["Language"] != language or existing_record["Meaning"] != meaning:
                id = len(elements) + 1
                elements[id] = {
                    "Id": id,
                    "Element": element,
                    "Language": language,
                    "Meaning": meaning,
                    "Frequency": 1,
                }
            else:
                existing_record["Frequency"] += 1
                if existing_record["Language"] is None and language is not None:
                    existing_record["Language"] = language
                if existing_record["Meaning"] is None and meaning is not None:
                    existing_record["Meaning"] = meaning

    rows = []
    for record in elements.values():
        rows.append(
            {
                "Id": record["Id"],
                "Element": record["Element"],
                "Language": record["Language"],
                "Meaning": record["Meaning"],
                "Frequency": record["Frequency"],
            }
        )

    return pd.DataFrame(rows, columns=["Id", "Element", "Language", "Meaning", "Frequency"])

def locateElement(elements: dict[int, ElementRecord], element_name: str) -> ElementRecord | None:
    """Locate the element in the dict. Since the dict is keyed by ID, we need to iterate through the values to find the element."""
    for record in elements.values():
        if record["Element"] == element_name:
            return record

    return None


def clean_text(value: str | None) -> str | None:
    """Remove any trailing or leading square brackets, speech marks and whitespace from the string."""
    if value is None:
        return None
    return value.strip("[]\"' ").strip()