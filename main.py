from pathlib import Path

import constants.constants as constants
from data_processing.process_csvs import save_combined_data
from data_processing.process_excel import process_excel_file
def import_and_process_data():
    """Import and process the data from the raw data files."""
    # Create the processed directory if it doesn't exist
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    # Check if the processed files already exist for the ordinance survey data, and if not, create them.
    if not Path("data/processed/opname_combined.csv").exists():
            save_combined_data(
                output_path=Path("data/processed/opname_combined.csv"),
                csv_folder=Path("data/raw/opname_csv_gb/Data"),
                header_file=Path("data/raw/opname_csv_gb/Doc/OS_Open_Names_Header.csv"),
                ignored_columns= constants.OS_IGNORED_COLUMNS
            )

    # Check if the processed files already exist for the office of national statistics data, and if not, create them.
    if not Path("data/processed/ons_combined.csv").exists():
            process_excel_file(
                excel_file_path=Path("data/raw/ons_data/datadownloadv2.xlsx"),
                ignored_columns= constants.ONS_IGNORED_COLUMNS,
                csv_file_path=Path("data/processed/ons_combined.csv")
            )

if __name__ == "__main__":
    import_and_process_data()