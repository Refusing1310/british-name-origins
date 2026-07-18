from pathlib import Path

from scripts.process_data import save_combined_os_data

# Check if the processed data files already exist, and if not, create them.
if not Path("data/processed/opname_combined.csv").exists():
        save_combined_os_data(
            output_path=Path("data/processed/opname_combined.csv"),
            csv_folder=Path("data/raw/opname_csv_gb/Data"),
            header_file=Path("data/raw/opname_csv_gb/Doc/OS_Open_Names_Header.csv"),
            ignored_columns=[]
        )