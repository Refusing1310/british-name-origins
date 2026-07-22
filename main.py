from pathlib import Path

import geopandas as gpd
import pandas as pd


import constants.constants as constants
from data_processing.process_csvs import process_kepn_data, save_combined_data
# from data_processing.process_excel import process_excel_file
from data_processing.convert_to_gdf import convert_to_geo_dataframe
from etymology.place_name_parser import parse_place_names
def import_and_process_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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
    # NOTE - this is not currently used in the script, but is included for future use if needed.
    # reprocess = input("Do you want to reprocess the office of national statistics place names data? (y/n): ").strip().lower()
    # if reprocess == "y":
        # if Path("data/processed/ons.csv").exists():
        #     Path("data/processed/ons.csv").unlink()

    # Check if the processed files files already exist for the key english place names data, and if not, create them.
    if not Path("data/processed/ground_truth.csv").exists() or not Path("data/processed/elements.csv").exists():
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
        geo_df = gpd.read_file("data/processed/ordinance_survey_gdf.csv")
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

    # Check if the processed files already exist for the office of national statistics data, and if not, create them.
    # NOTE - this is not currently used in the script, but is included for future use if needed.
    # if not Path("data/processed/ons.csv").exists():
    #     office_of_national_statistics_df = process_excel_file(
    #         excel_file_path=Path("data/raw/ons_data/datadownloadv2.xlsx"),
    #         ignored_columns= constants.ONS_IGNORED_COLUMNS,
    #         csv_file_path=Path("data/processed/ons.csv")
    #     )
    # else:
    #     office_of_national_statistics_df = Path("data/processed/ons.csv")

    # geo_df = parse_place_names(geo_df, Path("data/processed/aliases.csv"))

    # Store in csv file to prevent having to reprocess the data every time the script is run.
    # geo_df.to_csv("data/processed/ordinance_survey_gdf.csv", index=False)

    
    return (geo_df, ground_truth_df, elements_df)

if __name__ == "__main__":
    (geo_df, ground_truth_df, elements_df) = import_and_process_data()