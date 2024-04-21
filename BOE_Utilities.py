#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# -------------------------------------------------------------------------------
# Import additional Python functionality / various libraries
# -------------------------------------------------------------------------------

import pandas as pd
import numpy as np
from scipy.stats import zscore
import pickle

# -------------------------------------------------------------------------------
# Define function that loads and combines tabs from the source xlsx file
# -------------------------------------------------------------------------------

def create_combined_dataframe(file_name):
    try:
        # Obtain list of sheet names ("tabs") from the source Excel file.
        print("Sheet names in the Excel file:")
        excel_file = pd.ExcelFile(file_name)
        sheet_names = excel_file.sheet_names
        print(sheet_names)
        
        dfs = []  # List to store dataframes from each sheet
        
        # Iterate through each sheet in the Excel file
        for sheet_name in sheet_names:
            print(f"Processing sheet: {sheet_name}")
            # Read the sheet into a pandas dataframe
            # header = 4 (based on  manual inspection of file)
            df = pd.read_excel(file_name, sheet_name=sheet_name, header=4)
            
            # Slice off a single, superfluous row from the resulting dataframe (based on manual inspection of file)
            df = df[1:]
            
            # The "time period" column shall be the index for each dataframe (based on  manual inspection of file)
            df.set_index('Time period and dataset code row', inplace=True)
            clean_index_name = "TimePeriod"
            df.index.name = clean_index_name
            
            # Rename columns with suffix indicating the source sheet
            df.columns = [f'{col} (Sheet_{sheet_name})' for col in df.columns]
        
            # add the newly loaded dataframe to the list of dataframes ("dfs")
            dfs.append(df)
            print("Dataframe loaded successfully.")
                
        # Concatenate all dataframes into a single dataframe
        dfs_combined = pd.concat(dfs, axis=1, join='outer')
        print(f"{len(dfs)} Dataframes combined successfully.")
        return dfs_combined
        
    except Exception as e:
        print(f"Error loading Excel data: {str(e)}")
        return None

# -------------------------------------------------------------------------------
# Define function that tidies up the combined dataframe
# -------------------------------------------------------------------------------

def tidy_the_dataframe(df):

    try:
        # Convert the format of the index to be easily recognized by Python as "datetime" format
        df.index = df.index.str.replace(' ', '-')  # Replace spaces with dashes
        df.index = pd.to_datetime(df.index)        # Convert index to datetime format

        print("Index converted to datetime format successfully.")
    except Exception as e:
        print(f"Error occurred while converting index to datetime format: {e}")

    try:
        # Set datatype for all columns to floating
        df = df.apply(pd.to_numeric, errors='coerce').astype(float)

        print("Columns converted to floating point numbers successfully.")
    except Exception as e:
        print(f"Error occurred while converting columns to floating point numbers: {e}")

    return df

# -------------------------------------------------------------------------------
# Define function that amends the column names of the combined dataframe
# -------------------------------------------------------------------------------

def rename_columns(df, column_mapping):

    try:
        # Apply column renaming using the provided mapping
        df = df.rename(columns=column_mapping)
        print("Columns renamed successfully.")
        return df
    
    except Exception as e:
        print("An error occurred while renaming columns:", e)
        return None
    
# -------------------------------------------------------------------------------
# Define function that creates duplicate dataframes that show values as % change
# -------------------------------------------------------------------------------

def create_percentage_change_df(df, shift_value):
    try:
        # Copy the input DataFrame
        df_copy = df.copy()
        
        # Calculate percentage changes versus the specified shift value
        df_copy = ((df_copy / df_copy.shift(shift_value)) - 1) * 100
        
        # Calculate z-score for the 'GDP_Total_MarketPrices' column
        df_copy['Zscore'] = zscore(df_copy['GDP_Total_MarketPrices'], nan_policy='omit')
        
        # Clip z-score values
        df_copy['Zscore'] = np.clip(df_copy['Zscore'], -4, 4)
        
        # Return the resulting DataFrame
        return df_copy
    except Exception as e:
        print(f"An error occurred whilst creating percentage change df: {e}")
        return None

