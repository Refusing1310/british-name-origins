from pathlib import Path

import constants
from scripts.process_data import save_combined_data

# Check if the processed files already exist for the ordinance survey data, and if not, create them.
if not Path("data/processed/opname_combined.csv").exists():
        save_combined_data(
            output_path=Path("data/processed/opname_combined.csv"),
            csv_folder=Path("data/raw/opname_csv_gb/Data"),
            header_file=Path("data/raw/opname_csv_gb/Doc/OS_Open_Names_Header.csv"),
            ignored_columns= constants.OS_IGNORED_COLUMNS
        )