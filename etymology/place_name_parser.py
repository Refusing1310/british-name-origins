import pandas as pd
from pathlib import Path
def parse_place_names(geo_df: pd.DataFrame, aliases_file: Path) -> pd.DataFrame:
    """Parse the place names in the GeoDataFrame, splitting them into suffixes, prefix and root."""
    # TODO: replace with better algorithm later, e,g trie or ahocorasick for better performance.
    # Iterate over each row in the GeoDataFrame and parse the place name
    for index, row in geo_df.iterrows():
        place_name = row["NAME"]
        # normalize the place name to lower case for matching
        place_name_lower = place_name.lower()
        # remove punctuation and whitespace for matching
        place_name_lower = ''.join(e for e in place_name_lower if e.isalnum() or e.isspace())
        
        elements = find_elements(place_name_lower, aliases_file)
    return geo_df

def find_elements(place_name: str, aliases_file: Path) -> list[str]:
    """Find the elements (roots, suffixes, prefixes) in the place name."""
    # Using aliases.csv, find the elements in the place name, and return them as a list of strings.
    aliases_df = pd.read_csv(aliases_file)
    found_elements = []
    for _, row in aliases_df.iterrows():
        alias = row["alias"]
        # Check if the alias is in the place name
        if alias.lower() in place_name:
            found_elements.append(alias)
    return found_elements