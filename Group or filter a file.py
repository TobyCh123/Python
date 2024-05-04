"""
@author: ChallisT
@date: 10/04/2024

Script to read the output of the RST_weighted_euros_adjustable.py script
The output of that file is often too large to maninuplate in excel
This should help filter and pick out the info you want
Am happy to add more useability. Just ask :)

- Added functionality to compare two files (29/04/2024)
"""

import pandas as pd
import datetime


# Asks the user the inputs for the grouping
# TODO adjust this function so it works on any file i.e. same as filtering
def get_group():
    print("="*60, "\nWhat would you like to group by?")
    group_descriptions = {
        '1': 'Year',
        '2': 'Period',
        '3': 'Weight_Scheme',
        '4': 'Region',
        '5': 'Shop',
        '6': 'Shop_Group',
        '7': 'Custom_Grouping',
        '8': 'Validation_Field',
    }

    for key, value in group_descriptions.items():
        print(f"{key}. {value}")

    print('''
Enter as many as you want separated by comma.
You probably always want to include period,
if you include too many the file will be too big still
Input should be like 2, 6, 7
          ''')
    user_input = input('Option: ')
    group_numbers = [item.strip() for item in user_input.split(',')]
    group_descriptions_list = [
        group_descriptions[num] for num in group_numbers]
    return group_descriptions_list


# Groups the dataframe based on the inputs
# Currently sums on Euros, can change to buyers if you wish
def group_df(df):
    args = get_group()
    print("Grouping")
    print(args)
    df.reset_index(inplace=True, drop=True)
    grouped_df = df.groupby(args)['Euros'].sum().reset_index()
    return grouped_df


# Calculates all the KWP periods inbetween the range given
def get_period_list(timeframe):
    period_list = []
    parts = timeframe.split("-")
    parts = [part.strip() for part in parts]
    first_period = int(parts[0])
    last_period = int(parts[1])

    while first_period < last_period + 1:
        period_list.append(first_period)
        year = int(first_period/100)
        per = first_period - (100*year)
        if per == 13:
            first_period += 88
        else:
            first_period += 1
    return period_list


# Asks the user the inputs for the filter
def get_filter(df):
    col_name = input("""Enter column to filter
      - 'X' to finish,
      - '-' to restart

      Input: """)
    if col_name.upper() == 'X':
        return 'X'

    elif col_name == "-":
        return '-'

    elif col_name not in df.columns:
        print("Column not found. Please enter a valid column name.")
        print("These are your options...")
        print(df.columns)
        return '#'

    return col_name


# Gets the value to filter to
def get_filter_value(df, col_name):
    print(f"""\nEnter the value to filter for {col_name}
      - 1 to see options
      - For Period use format YYYYPP-YYYYPP to specify a range
      """)
    while True:
        value = input("Input: ")
        if value == '1':
            print(df[col_name].unique())

        elif '-' in value and col_name == "Period":
            values = get_period_list(value)
            break

        else:
            values = [v.strip() for v in value.split(',')]
            values = [int(v) if v.isdigit() else v for v in values]
            print(values)
            break

    return values


# filters the dataframe based on the inputs
def filter_df(df):
    filtered_df = df
    print("="*60, "\nThe file columns are...")
    print(df.columns)
    while True:
        temp_df = filtered_df
        col_name = get_filter(temp_df)

        if col_name == 'X':
            break

        elif col_name == '-':
            filtered_df = df
            print("dataframe reset")
            print("="*60)
            continue

        elif col_name == '#':
            continue

        value = get_filter_value(temp_df, col_name)
        temp_df = temp_df[temp_df[col_name].isin(value)]
        if len(temp_df) == 0:
            print("That outputs an empty df, check your value")
        else:
            filtered_df = temp_df
            print(f"New df: {len(filtered_df)}")
    return filtered_df


# Reads the CSV and creates a year column
def prep_df(filename):
    df = pd.read_csv(filename)
    print(f'file: {filename} read, first 5 columns...')
    print(df.head())
    print(f"The file contains: {len(df)} rows")

    # Create a year column
    # The file this script was designed to read has a period column
    # As does almost all data we work with
    df['Period'] = df['Period'].astype(str)
    df['Year'] = df['Period'].str[:4].astype(int)
    df['Period'] = df['Period'].astype(int)
    return df


# Saves the file, uses hour minute for unique filename
def save(df):
    filename = input("Enter the filename to save as: ")
    print("Saving...")
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d")
    full_filename = f"{filename}_{timestamp}.xlsx"
    df.to_excel(full_filename, index=False)


# Creates the new dataframe based on user options
def generate_new_df(df):
    output_df = df

    while True:
        print("\nWhat would you like to do?")
        print('''
          1: Filter by ...
          2: Group by...
          X: Continue''')
        userInput = input("Option: ")

        temp_df = output_df
        if userInput == '1':
            output_df = filter_df(temp_df)

        elif userInput == '2':
            output_df = group_df(temp_df)

        elif userInput.upper() == 'X':
            if len(output_df) >= 1048576:
                print(f"The length is {len(output_df)}, this is too big still")
                continue
            else:
                break
    return output_df


# Merge the two dataframe outputs on all but last column i.e. summed value
def merge_dfs(df1, df2):
    merge_columns = list(df1.columns[:-1])
    merged_df = pd.merge(df1, df2,
                         how='outer',
                         on=merge_columns)
    return merged_df


# Calculates difference between the last two columns i.e. the summed value
def calculate_differences(df):
    print("Calculating differences...")
    last_col = df.iloc[:, -1].astype(float)
    second_last_col = df.iloc[:, -2].astype(float)
    df['Differences'] = round((last_col / second_last_col) - 1, 5)
    return df


filename_input = input("Enter the name of the file you would like to read: ")
first_data_df = generate_new_df(prep_df(f"{filename_input}"))

two_files_q = input("Would you like to compare with another file? (Y/N):  ")

if two_files_q.upper() == 'Y':
    filename2_input = input("Enter the second filename: ")
    second_data_df = generate_new_df(prep_df(f"{filename2_input}"))

    merged_df = merge_dfs(first_data_df, second_data_df)
    final_df = calculate_differences(merged_df)
else:
    final_df = first_data_df

save(final_df)
