from pathlib import Path

import constants.constants as constants
from data_processing.process_csvs import save_combined_data
from data_processing.process_excel import process_excel_file
from data_processing.combine_data import combine_dataframes
def import_and_process_data() :
    """Import and process the data from the raw data files."""
    # Create the processed directory if it doesn't exist
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    # Try to load the processed data from the CSV files, and if they don't exist, create them.
    ordinance_survey_df = open(Path("data/processed/ordinance_survey_combined.csv"), "r") if Path("data/processed/ordinance_survey_combined.csv").exists() else None
    if ordinance_survey_df is None:
        ordinance_survey_df = save_combined_data(
            output_path=Path("data/processed/ordinance_survey_combined.csv"),
            csv_folder=Path("data/raw/opname_csv_gb/Data"),
            header_file=Path("data/raw/opname_csv_gb/Doc/OS_Open_Names_Header.csv"),
            ignored_columns= constants.OS_IGNORED_COLUMNS
        )

    # Check if the processed files already exist for the office of national statistics data, and if not, create them.
    office_of_national_statistics_df = open(Path("data/processed/ons_combined.csv"), "r") if Path("data/processed/ons_combined.csv").exists() else None
    if office_of_national_statistics_df is None:
        process_excel_file(
            excel_file_path=Path("data/raw/ons_data/datadownloadv2.xlsx"),
            ignored_columns= constants.ONS_IGNORED_COLUMNS,
            csv_file_path=Path("data/processed/ons_combined.csv")
        )
    combine_dataframes(ordinance_survey_df, office_of_national_statistics_df, Path("data/processed/combined_data.csv"))

if __name__ == "__main__":
    import_and_process_data()