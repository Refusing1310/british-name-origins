def parse_place_names(geo_df):
    """Parse the place names in the GeoDataFrame, splitting them into suffixes, prefix and root."""
    
    for index, row in geo_df.iterrows():
        name = row['NAME1']
        parsed_name = parse_name(name)
        geo_df.at[index, 'PREFIX'] = parsed_name['prefix']
        geo_df.at[index, 'ROOT'] = parsed_name['root']
        geo_df.at[index, 'SUFFIX'] = parsed_name['suffix']
    return geo_df


def parse_name(name):
    """Parse a single place name into its prefix, root, and suffix."""
    # Define known prefixes and suffixes
    known_prefixes = ['North', 'South', 'East', 'West', 'Upper', 'Lower']
    known_suffixes = ['ton', 'ham', 'ford', 'bury', 'ley', 'worth', 'field', 'bridge']

    # Initialize the components
    prefix = ''
    root = name
    suffix = ''

    # Check for known prefixes
    for p in known_prefixes:
        if name.startswith(p + ' '):
            prefix = p
            root = name[len(p) + 1:]  # Remove the prefix and the space
            break

    # Check for known suffixes
    for s in known_suffixes:
        if root.endswith(s):
            suffix = s
            root = root[:-len(s)]  # Remove the suffix
            break

    return {'prefix': prefix, 'root': root.strip(), 'suffix': suffix}