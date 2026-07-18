from pathlib import Path

import geopandas as gpd
import pandas as pd


import constants.constants as constants
from data_processing.process_csvs import save_combined_data
from data_processing.process_excel import process_excel_file
from data_processing.convert_to_gdf import convert_to_geo_dataframe
from etymology.place_name_parser import parse_place_names
def import_and_process_data() :
    """Import and process the data from the raw data files."""
    # Create the processed directory if it doesn't exist
    Path("data/processed").mkdir(parents=True, exist_ok=True)

    # Check if the geo dataframe already exists, and if not, create it.
    if Path("data/processed/ordinance_survey_gdf.csv").exists():   
        # Load the existing GeoDataFrame from the CSV file
        return gpd.read_file("data/processed/ordinance_survey_gdf.csv")
    # Otherwise, process the data and create the GeoDataFrame
    # Check if files already exist for the ordinance survey data, and if not, create them.
    if not Path("data/processed/ordinance_survey.csv").exists():
        ordinance_survey_df = save_combined_data(
            output_path=Path("data/processed/ordinance_survey.csv"),
            csv_folder=Path("data/raw/opname_csv_gb/Data"),
            header_file=Path("data/raw/opname_csv_gb/Doc/OS_Open_Names_Header.csv"),
            ignored_columns= constants.OS_IGNORED_COLUMNS
        )
    else:
        ordinance_survey_df = Path("data/processed/ordinance_survey.csv")

    # Check if the processed files already exist for the office of national statistics data, and if not, create them.
    # NOTE - this is not currently used in the script, but is included for future use if needed.
    # if not Path("data/processed/ons_combined.csv").exists():
    #     office_of_national_statistics_df = process_excel_file(
    #         excel_file_path=Path("data/raw/ons_data/datadownloadv2.xlsx"),
    #         ignored_columns= constants.ONS_IGNORED_COLUMNS,
    #         csv_file_path=Path("data/processed/ons_combined.csv")
    #     )
    # else:
    #     office_of_national_statistics_df = Path("data/processed/ons_combined.csv")

    geo_df = convert_to_geo_dataframe(ordinance_survey_df)
    parsed_geo_df = parse_place_names(geo_df)

    # Store in csv file to prevent having to reprocess the data every time the script is run.
    parsed_geo_df.to_csv("data/processed/ordinance_survey_gdf.csv", index=False)
    return parsed_geo_df

if __name__ == "__main__":
    df = import_and_process_data()