import pandas as pd



def parse_place_names(geo_df) -> pd.DataFrame:
    """Parse the place names in the GeoDataFrame, splitting them into suffixes, prefix and root."""
    # TODO: replace with better algorithm later, e,g trie or ahocorasick for better performance.

    # Load the suffixes and prefixes from the CSV file into a DataFrame
    suffixes = pd.read_csv("data/processed/suffixes.csv")
    prefixes = pd.read_csv("data/processed/prefixes.csv")
    
    # Sort the suffixes and prefixes by priority in descending order to ensure longer matches are found first
    suffixes = suffixes.sort_values(by="priority", ascending=False)
    prefixes = prefixes.sort_values(by="priority", ascending=False)

    # Iterate over each row in the GeoDataFrame and parse the place name
    for index, row in geo_df.iterrows():
        place_name = row["NAME"]
        # normalize the place name to lower case for matching
        place_name_lower = place_name.lower()
        # remove punctuation and whitespace for matching
        place_name_lower = ''.join(e for e in place_name_lower if e.isalnum() or e.isspace())
        suffix = find_suffix(place_name_lower, suffixes)
        prefix = find_prefix(place_name_lower, prefixes)
        root = place_name

        # Remove the  prefix and suffix from the root if they were found
        if prefix is not None:
            root = root[len(prefix[0]):]
        if suffix is not None:
            root = root[:-len(suffix[0])]
        if prefix is not None:
            geo_df.at[index, "prefix"] = prefix[0]
            geo_df.at[index, "prefix_language"] = prefix[1]
            geo_df.at[index, "prefix_confidence"] = prefix[2]
        if suffix is not None:
            geo_df.at[index, "suffix"] = suffix[0]
            geo_df.at[index, "suffix_language"] = suffix[1]
            geo_df.at[index, "suffix_confidence"] = suffix[2]
        
        geo_df.at[index, "root"] = root.strip()

    return geo_df

def find_suffix(place_name, suffixes):
    """Find the longest matching suffix in the place name."""
    for _, row in suffixes.iterrows():
        if place_name.endswith(row.element.lower()):
            return (row.element, row.language, row.confidence)
    return None

def find_prefix(place_name, prefixes):
    """Find the longest matching prefix in the place name."""
    for _, row in prefixes.iterrows():
        if place_name.startswith(row.element.lower()):
            return (row.element, row.language, row.confidence)
    return None