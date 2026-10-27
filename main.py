from pathlib import Path

import geopandas as gpd
import pandas as pd


import constants.constants as constants
from data_processing.process_csvs import process_kepn_data, save_combined_data
from data_processing.convert_to_gdf import convert_to_geo_dataframe, load_processed_geo_dataframe
from etymology.place_name_parser import parse_place_names
from data_processing.produce_aliases import build_aliases_csv
def import_and_process_data() -> gpd.GeoDataFrame:
    """Import and process the data from the raw data files."""
    # Create the processed directory if it doesn't exist
    Path("data/processed").mkdir(parents=True, exist_ok=True)

    # Ask the user if they want to reprocess the data or use the existing processed files.
    reprocess = input("Do you want to reprocess the ordinance survey data? (y/n): ").strip().lower()
    if reprocess == "y":
        if Path("data/processed/ordinance_survey_combined.csv").exists():
            Path("data/processed/ordinance_survey_combined.csv").unlink()
        if Path("data/processed/ordinance_survey_gdf.csv").exists():
            Path("data/processed/ordinance_survey_gdf.csv").unlink()
    reprocess = input("Do you want to reprocess the english place names data? (y/n): ").strip().lower()
    if reprocess == "y":
            if Path("data/processed/ground_truth.csv").exists():
                Path("data/processed/ground_truth.csv").unlink()
            if Path("data/processed/elements.csv").exists():
                Path("data/processed/elements.csv").unlink()
            if Path("data/processed/non_derivation_starters.csv").exists():
                Path("data/processed/non_derivation_starters.csv").unlink()

    # Check if the processed files files already exist for the key english place names data, and if not, create them.
    rebuild_elements = (not Path("data/processed/ground_truth.csv").exists()
                        or not Path("data/processed/elements.csv").exists())
    if rebuild_elements:
        ground_truth_df, elements_df = process_kepn_data(
            csv_folder=Path("data/raw/kepn/"),
            output_folder=Path("data/processed/"),
        )
    else:
        ground_truth_df = pd.read_csv(Path("data/processed/ground_truth.csv"))
        elements_df = pd.read_csv(Path("data/processed/elements.csv"))
    
    # Check if the geo dataframe already exists, and if not, create it.
    if Path("data/processed/ordinance_survey_gdf.csv").exists():   
        # Load the existing GeoDataFrame from the CSV file
        geo_df = load_processed_geo_dataframe(Path("data/processed/ordinance_survey_gdf.csv"))
    # Otherwise, process the data and create the GeoDataFrame
    else:
        # Check if files already exist for the ordinance survey data, and if not, create them.
        if not Path("data/processed/ordinance_survey_combined.csv").exists():
            ordinance_survey_df = save_combined_data(
                output_path=Path("data/processed/ordinance_survey_combined.csv"),
                csv_folder=Path("data/raw/opname_csv_gb/Data"),
                header_file=Path("data/raw/opname_csv_gb/Doc/OS_Open_Names_Header.csv"),
                ignored_columns= constants.OS_IGNORED_COLUMNS,
            )
        else:
            ordinance_survey_df = Path("data/processed/ordinance_survey_combined.csv")
        geo_df = convert_to_geo_dataframe(ordinance_survey_df)

    # TODO: integrate Office for National Statistics imports when supported.

    # Create aliases.csv from elements.csv
    # Aliases must be rebuilt whenever their element source is rebuilt, even
    # if a previous run left an existing (now stale) aliases.csv behind.
    if rebuild_elements or not Path("data/processed/aliases.csv").exists():
        # Create aliases.csv from elements.csv
        build_aliases_csv(elements_df, output_path=Path("data/processed/aliases.csv"))

    geo_df = parse_place_names(geo_df, elements_df, ground_truth_df)
    # Store in csv file to prevent having to reprocess the data every time the script is run.
    geo_df.to_csv("data/processed/ordinance_survey_gdf.csv", index=False)
    return geo_df

if __name__ == "__main__":
    import_and_process_data()