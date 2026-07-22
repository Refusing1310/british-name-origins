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
    # Sort by frequency in descending order, then by element name in ascending order
    elements_df = elements_df.sort_values(by=["Frequency", "Element"], ascending=[False, True])
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

    # Get non definition starters from file
    non_definition_starters_path = Path("data/processed/non_definition_starters.csv") 
    non_definition_starters: list[str] = []
    if non_definition_starters_path.exists():
        non_definition_starters = pd.read_csv(Path("data/processed/non_definition_starters.csv"), header=None).iloc[0].tolist()
    # Parse each row in the dataframe to extract elements and their meanings
    for _, row in df.iterrows():
        parse_row(row, elements, non_definition_starters)
    # Save updated non_definition_starters to file
    non_definition_starters_df = pd.DataFrame([non_definition_starters])
    non_definition_starters_df.to_csv(non_definition_starters_path, index=False, header=False)

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

def parse_row(row: pd.Series, elements: dict[int, ElementRecord], non_definition_starters: list[str]) -> None:
    languages = ["Old English", "Middle English", "Old Norse", "Latin", "French", "Welsh", "Irish", "Scottish Gaelic", "Cornish", "Breton", "German", "Dutch", "Italian", "Spanish", "Portuguese", "Greek", "Arabic", "Hebrew", "C"]
    derivations = row["Derivation"]
    if pd.isna(derivations):
        return # Skip processing if derivations is NaN
    # Split the derivations into individual elements (sometimes a semicolon is used in a definition which complicates matters)
    derivations_list = str(derivations).split(";")
    for i in range(len(derivations_list)):
        derivation = clean_text(derivations_list[i])
        if not derivation or derivation == "":
            # Skip processing if the derivation is empty
            continue
        first_word = derivation.split()[0].strip("[]\"' ")
        if first_word in non_definition_starters:
            # Skip processing if the derivation is a known non-definition starter
            continue
        valid_derivation = False
        # Keep checking the next derivation until we find a valid one or run out of derivations, joining them together if necessary. 
        # This is to handle cases where a semicolon is used in a definition, which can cause the derivation to be split incorrectly.
        while not valid_derivation:
            if i + 1 < len(derivations_list):
                next_derivation = clean_text(derivations_list[i + 1])
                if next_derivation:
                    # If the first word of the next derivation is one of these identifiers, then it's part of the current definition and not a new derivation. Append it to the current derivation.
                    first_word = next_derivation.split()[0].strip("[]\"' ")
                    if first_word in non_definition_starters:
                        # This IS a known non-definition starter, so merge it
                        derivation += "; " + next_derivation
                        i += 1  # Skip the next derivation since we've merged it
                    else:
                        # There are special cases and require special handling (one of the only cases where the definition might not have a language associated with it). 
                        # If the first word is one of these, then we can assume it's a separate derivation and not part of the current definition. We can stop merging and move on to the next derivation.
                        if first_word in ["Personal", "River-name", "Place-name", "Obscure", "Family-name", "Tribal-name"]:
                            valid_derivation = True
                            break
                        # The word isn't a known non-definition starter, so check if it contains any of the known languages. If it doesn't, then it's part of the current definition. 
                        # If it does contain a known language, then it's a new derivation and we should stop merging.
                        contains_language = False
                        for lang in languages:
                            if lang in next_derivation:
                                contains_language = True
                                valid_derivation = True
                                break
                        if not contains_language:
                            # Add it as a non-definition starter for future reference
                            if first_word == "Personal":
                                print(f"Adding non-definition starter: {first_word}, derivation: {derivation}, all derivations: {derivations_list}")
                            non_definition_starters.append(first_word)
                            derivation += "; " + next_derivation
                            i += 1  # Skip the next derivation since we've merged it
            else:
                valid_derivation = True  # No more derivations to check, so we're done merging
        match first_word:
            case "Personal":
                meaning = derivation 
                # More likely to come from etymology than place name, so check etymology first. If not found, then check place name.
                if row["Etymology"] and not pd.isna(row["Etymology"]):
                    element = get_name_from_string(row["Etymology"])
                else:
                    element = get_name_from_string(row["PlaceName"])
            case "River-name":
                meaning = derivation
                element = row["PlaceName"]
            case "Place-name":
                meaning = derivation
                element = row["PlaceName"]
            case "Obscure":
                meaning = derivation
                element = row["PlaceName"]
            case _:
                if len(derivation.split(" - ", 1)) < 2:
                    # Doesn't have a meaning
                    element = derivation.split()[0] # Get the first word as the element
                    meaning = None
                else:
                    head, meaning = derivation.split(" - ", 1)
                    head = clean_text(head) or ""
                    meaning = clean_text(meaning)
                    head_parts = head.split()
                    element = head_parts[0]
        language = get_language_from_derivation(derivation, languages)
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
    

def get_language_from_derivation(derivation: str, languages: list[str]) -> str | None:
    """Extract the language from the derivation string."""
    for lang in languages:
        if lang in derivation:
            return lang
    return None

def get_name_from_string(string: str) -> str:
    """Extract the name from the etymology string."""
    # Name either starts with an asterisk, ends with 's, or is proceeded by "with"
    if string == "":
        return ""
    words = string.split()
    for i in range(len(words)):
        word = words[i]
        if word.startswith("*") or word.endswith("'s"):
            return word.strip("'s")
        if i > 0 and words[i - 1].lower() == "with":
            return word.strip("'s")
    return ""