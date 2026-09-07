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
    Reconstructed: bool
    
def parse_elements(df: pd.DataFrame) -> pd.DataFrame:
    """Parse the elements (roots, suffixes, prefixes) from the KEPN dataset."""
    if "Derivation" not in df.columns:
        raise ValueError("The 'Derivation' column is missing from the dataframe.")

    elements: dict[int, ElementRecord] = {}

    # Get non derivation starters from file
    non_derivation_starters_path = Path("data/processed/non_derivation_starters.csv") 
    non_derivation_starters: list[str] = []
    if non_derivation_starters_path.exists():
        try:
            non_derivation_starters = pd.read_csv(non_derivation_starters_path, header=None).iloc[0].tolist()
        except pd.errors.EmptyDataError:
            non_derivation_starters = []
    # Parse each row in the dataframe to extract elements and their meanings
    for _, row in df.iterrows():
        parse_row(row, elements, non_derivation_starters)
    # Save updated non_derivation_starters to file
    non_derivation_starters_df = pd.DataFrame([non_derivation_starters])
    non_derivation_starters_df.to_csv(non_derivation_starters_path, index=False, header=False)

    rows = []
    for record in elements.values():
        rows.append(
            {
                "Id": record["Id"],
                "Element": record["Element"],
                "Language": record["Language"],
                "Meaning": record["Meaning"],
                "Frequency": record["Frequency"],
                "Reconstructed": record["Reconstructed"],
            }
        )

    return pd.DataFrame(rows, columns=["Id", "Element", "Language", "Meaning", "Frequency", "Reconstructed"])

def locateElement(
    elements: dict[int, ElementRecord],
    element_name: str,
    language: str | None,
    meaning: str | None,
    reconstructed: bool | None
) -> ElementRecord | None:
    """Locate the exact element record in the dict.

    Multiple records can share the same element name when the language or meaning differs,
    so we match the full tuple instead of returning the first same-name row.
    """
    for record in elements.values():
        if (
            record["Element"] == element_name
            and record["Language"] == language
            and record["Meaning"] == meaning
            and record["Reconstructed"] == reconstructed
        ):
            return record

    return None


def clean_text(value: str | None) -> str | None:
    """Remove any trailing or leading square brackets, speech marks and whitespace from the string."""
    if value is None:
        return None
    return value.strip("[]\"' ").strip()

def parse_row(row: pd.Series, elements: dict[int, ElementRecord], non_definition_starters: list[str]) -> None:
    languages = ["Modern English", "Old English", "Middle English", "Old Norse", "Latin", "French", "Welsh", "Irish", "Scottish Gaelic", "Cornish", "Breton", "German", "Dutch", "Italian", "Spanish", "Portuguese", "Greek", "Arabic", "Hebrew", "C", "Unknown", "Other"]
    special_cases = ["personal", "river-name", "obscure", "family-name", "tribal", "tribal-name", "place", "place-name", "family", "saint's", "saint", "water", "land", "mill", "church"]
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
        current_first_word = derivation.split()[0].strip("()[]\"' ")
        if current_first_word in non_definition_starters:
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
                    next_first_word = next_derivation.split()[0].strip("()[]\"' ").lower()
                    if next_first_word in non_definition_starters:
                        # This IS a known non-definition starter, so merge it
                        derivation += "; " + next_derivation
                        i += 1  # Skip the next derivation since we've merged it
                    else:
                        # If the next derivation is just one word, then it's a new derivation, simply the name of a location
                        if len(next_derivation.split()) == 1:
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
                        # There are special cases and require special handling (one of the only cases where the definition might not have a language associated with it). 
                        # If the first word is one of these, then we can assume it's a separate derivation and not part of the current definition. We can stop merging and move on to the next derivation.
                        if next_first_word in special_cases:
                            valid_derivation = True
                            break
                        if not contains_language:
                            # Add it as a non-definition starter for future reference
                            non_definition_starters.append(next_first_word)
                            derivation += "; " + next_derivation
                            i += 1  # Skip the next derivation since we've merged it
            else:
                valid_derivation = True  # No more derivations to check, so we're done merging
        element = None
        meaning = None
        match current_first_word.lower():
            # TODO - improve meaning parsing for these special cases, as currently they are just set to the derivation text a lot of the time which isn't very useful.
            case "personal":
                meaning = derivation
                # More likely to come from etymology than place name, so check etymology first. If not found, then check place name.
                if row["Etymology"] and not pd.isna(row["Etymology"]):
                    element = get_name_from_string(row["Etymology"])
                elif row["PlaceName"] and not pd.isna(row["PlaceName"]):
                    element = get_name_from_string(row["PlaceName"])
                else:
                    element = row["PlaceName"]
            case "river-name":
                meaning = derivation
                # Find word river in etymology and get the next word as the element. If not found, then check place name.
                if row["Etymology"] and not pd.isna(row["Etymology"]):
                    name = find_name_using_previous(["river"], [row["Etymology"]])
                    if name:
                        element = name
                if not element:
                    element = row["PlaceName"]
            case "obscure":
                meaning = row["Etymology"]
                element = clean_text(row["PlaceName"])
            case "saint's" | "saint":
                meaning = derivation
                # Find word St or Saint in etymology or place name and get the next word as the element.
                if row["Etymology"] and not pd.isna(row["Etymology"]) and row["PlaceName"] and not pd.isna(row["PlaceName"]):
                    name = find_name_using_previous(["St", "Saint", "St."], [row["Etymology"], row["PlaceName"]])
                    if name:
                        element = name
                if not element:
                    element = clean_text(row["PlaceName"])
            case "family" | "family-name":
                # TODO - element will be after the word "family" in the derivation, and meaning might be the rest of the derivation after the element.
                name = find_name_using_previous(["by", "family"], [derivation])
                meaning = derivation
                element = clean_text(row["PlaceName"])
            case "tribal" | "tribal-name":
                # TODO - This one is very complicated and has many different cases
                meaning = derivation
                element = clean_text(row["PlaceName"])
            case "place" | "place-name":
                # TODO - again very complicated and has many different cases
                meaning = derivation
                element = clean_text(row["PlaceName"])
            case "land":
                # TODO
                meaning = derivation
                element = clean_text(row["PlaceName"])
            case "water":
                # TODO
                meaning = derivation
                element = clean_text(row["PlaceName"])
            case "mill":
                # TODO
                meaning = derivation
                element = clean_text(row["PlaceName"])
            case "church":
                # TODO
                meaning = derivation
                element = clean_text(row["PlaceName"])
            case _:
                if len(derivation.split(" - ", 1)) < 2:
                    # Doesn't have a meaning
                    element = derivation.split()[0] # Get the first word as the element
                    if element in special_cases:
                        # If the first word is one of these special cases, then something has gone wrong, should have been caught by the previous checks. Skip this derivation and move on to the next one.
                        print(f"Warning: Skipping derivation '{derivation}' for place name '{row['PlaceName']}' as it starts with a special case word. (Should have been caught by previous checks.)")
                        continue
                    meaning = None
                else:
                    head, meaning = derivation.split(" - ", 1)
                    head = clean_text(head) or ""
                    meaning = clean_text(meaning)
                    head_parts = head.split()
                    element = head_parts[0]
        element = clean_text(element)
        if not element or element == "":
            continue  # Skip processing if the element is empty 
        element = normalise_element(element)
        # In etymology, an asterisk indicates that the element is reconstructed. Remove it from the element name and set the reconstructed flag to True.
        if element.__contains__("*"):
            reconstructed = True
            element = element.replace("*", "")
        else:
            reconstructed = False
        language = get_language_from_derivation(derivation, languages)
        # If element contains a slash, then it represents two different spellings of the same element. Split it into two elements and add them both to the dict.
        if element.__contains__("/"):
            for sub_element in element.split("/"):
                add_element_to_dict(elements, sub_element, language, meaning, reconstructed)
        else:
            add_element_to_dict(elements, element, language, meaning, reconstructed)
    

def get_language_from_derivation(derivation: str, languages: list[str]) -> str | None:
    """Extract the language from the derivation string."""
    for lang in languages:
        if lang in derivation:
            return lang
    return None

def get_name_from_string(string: str) -> str:
    """Extract the name from the etymology string."""
    # TODO improve this function to handle more cases, such as when the name is preceded by "with" or "was", or when the name is in parentheses.
    # Name either starts with an asterisk, ends with 's, or is proceeded by "with"
    if string == "":
        return ""
    words = string.split()
    # Priority queue of possible names, with the first one being the most likely to be the correct name.
    possible_names = []
    for i in range(len(words)):
        word = words[i]
        if word.startswith("*") or word.endswith("'s"):
            possible_names.append((word, 1))  # (name, priority)
        if i > 0 and words[i - 1].lower() in ["with", "was"]:
            possible_names.append((word, 2))  # (name, priority)
    # Sort by priority and return the first name
    possible_names.sort(key=lambda x: x[1])
    if possible_names and possible_names[0][0] == "the":
        # If the first possible name is "the", then it's probably not the correct name. Return the next possible name if it exists.
        return clean_text(possible_names[1][0]) or "" if len(possible_names) > 1 else ""
    return clean_text(possible_names[0][0]) or "" if possible_names else ""

def normalise_element(element: str) -> str:
    """Normalise the string by removing punctuation and converting to lowercase."""
    # Remove punctuation and 's, then convert to lowercase and strip whitespace
    return element.replace("'s", "").translate(str.maketrans("", "", ".,;:!?()[]{}\"'")).lower().strip()

def add_element_to_dict(elements: dict, element: str, language: str | None, meaning: str | None, reconstructed: bool) -> None:
    """Add the element to the elements dict, or update the frequency if it already exists."""
    existing_record = locateElement(elements, element, language, meaning, reconstructed)
    if existing_record is None:
            id = len(elements) + 1
            elements[id] = {
                "Id": id,
                "Element": element,
                "Language": language,
                "Meaning": meaning,
                "Frequency": 1,
                "Reconstructed": reconstructed,
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
            "Reconstructed": reconstructed,
        }
    else:
        existing_record["Frequency"] += 1

def find_name_using_previous(previous_words: list[str], texts: list[str]) -> str:
    """Find the name from the previous word in the texts."""
    word = ""
    for text in texts:
        if text is None or text == "" or text == "nan":
            continue
        etymology_words = text.split()
        for i in range(len(etymology_words)):
            if etymology_words[i].lower() in [word.lower() for word in previous_words] and i + 1 < len(etymology_words):
                word = etymology_words[i + 1]
                break
    return clean_text(word) or ""