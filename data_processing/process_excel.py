# Read the data from the excel file and save it to a csv file in the data/raw directory.
import pandas as pd


def process_excel_file(excel_file_path, ignored_columns, csv_file_path):
    # Read the excel file into a pandas dataframe
    df_towns = pd.read_excel(excel_file_path, sheet_name="Towns (5,000 to 225,000)")
    df_cities_and_london = pd.read_excel(excel_file_path, sheet_name="Cities (>225,000) and London")
    df_combined = pd.concat([df_towns, df_cities_and_london], ignore_index=True)

    # Clean the data by dropping the ignored columns and any rows with missing values.
    # The Excel year columns are stored as integers (e.g. 2001), while the ignored
    # list can include string names such as "2001", so remove any matching labels
    # from the DataFrame after normalising them to strings.
    columns_to_drop = []
    for column in ignored_columns:
        if column in df_combined.columns:
            columns_to_drop.append(column)
        else:
            column_str = str(column)
            matching_columns = [col for col in df_combined.columns if str(col) == column_str]
            columns_to_drop.extend(matching_columns)

    if columns_to_drop:
        df_combined.drop(columns=columns_to_drop, inplace=True)

    # Drop any rows with missing values
    df_combined.dropna(inplace=True)

    # Only keep rows where the age group is "TOTAL"
    df_combined = df_combined[df_combined['AGE GROUP'] == 'TOTAL']

    # Remove " BUA" from the "TOWN_2011NAME" column
    df_combined['TOWN_2011NAME'] = df_combined['TOWN_2011NAME'].str.replace(' BUA', '')

    # Remove excel row id column
    if 'Unnamed: 0' in df_combined.columns:
        df_combined.drop(columns=['Unnamed: 0'], inplace=True)

    # Remove Age group column
    if 'AGE GROUP' in df_combined.columns:
        df_combined.drop(columns=['AGE GROUP'], inplace=True)

    # Rename the "TOWN_2011NAME" column to "TOWN NAME"
    if 'TOWN_2011NAME' in df_combined.columns:
        df_combined.rename(columns={'TOWN_2011NAME': 'TOWN NAME'}, inplace=True)

    # Save the dataframe to a csv file
    df_combined.to_csv(csv_file_path, index=True, encoding='utf-8-sig')  # Use utf-8-sig to handle special characters