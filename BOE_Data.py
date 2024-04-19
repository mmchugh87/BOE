#!/usr/bin/env python
# coding: utf-8

# In[89]:


# -------------------------------------------------------------------------------
# Import additional Python functionality / various libraries
# -------------------------------------------------------------------------------

import pandas as pd
import numpy as np
from scipy.stats import zscore
import pickle

# -------------------------------------------------------------------------------
# Load and combine each tab from the source xlsx file
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
            # header = 4, based on visual inspection of the excel file
            df = pd.read_excel(file_name, sheet_name=sheet_name, header=4)
            
            # Slice off a single, superfluous row from the resulting dataframe (based on visual inspection of file)
            df = df[1:]
            
            # The "time period" column shall be the index for each dataframe.
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
    
# Run the function: create_combined_dataframe
file_name = 'Dashboard dataset.xlsx'
df_GDP = create_combined_dataframe(file_name)

# -------------------------------------------------------------------------------
# Tidy the resulting combined dataframe
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

# Run the function: tidy_the_dataframe
df_GDP = tidy_the_dataframe(df_GDP)

# -------------------------------------------------------------------------------
# Through manual inspection, propose alternative column names for clarity / brevity
# -------------------------------------------------------------------------------

column_mapping = {'Households: Final consumption expenditure (Sheet_GDP)': 'GDP_Component_Household_Spend', 
                  'General Government: Final consumption expenditure (Sheet_GDP)': 'GDP_Component_Gov_Spend',
                  'Gross fixed capital formation: Gross capital formation (Sheet_GDP)': 'GDP_Component_GFCF',
                  'Changes in inventories: Gross capital formation (Sheet_GDP)': 'GDP_Component_Inventories',
                  'Trade balance  (Sheet_GDP)': 'GDP_Component_TradeBalance',
                  'Other (Sheet_GDP)': 'GDP_Component_Other',
                  'Gross domestic product at market prices (Sheet_GDP)': 'GDP_Total_MarketPrices',
                  'Total: UK National (Sheet_Consumption)': 'Household_Total_Spend',
                  'Durable goods: UK Domestic (Sheet_Consumption)': 'Household_Component_Durables',
                  'Semi-durable goods: UK Domestic (Sheet_Consumption)': 'Household_Component_SemiDurables',
                  'Non-durable goods: UK Domestic (Sheet_Consumption)': 'Household_Component_NonDurables',
                  'Services: UK Domestic (Sheet_Consumption)': 'Household_Component_Services',
                  'Other (Sheet_Consumption)': 'Household_Component_Other'}

def rename_columns(df, column_mapping):

    try:
        # Apply column renaming using the provided mapping
        df = df.rename(columns=column_mapping)
        print("Columns renamed successfully.")
        return df
    
    except Exception as e:
        print("An error occurred while renaming columns:", e)
        return None

# Run the function: rename_columns
df_GDP = rename_columns(df=df_GDP, column_mapping=column_mapping)

# -------------------------------------------------------------------------------
# Manually identify meaningful groupings of columns
# -------------------------------------------------------------------------------

# Define a list of the columns that represent top level *components* of GDP.
GDP_Components = list(df_GDP.columns)[:6]

# Define a list of the columns that represent *components* of Household Spending.
Household_Components = list(df_GDP.columns)[-5:]

# -------------------------------------------------------------------------------
# Create and tweak duplicate dataframes, to feed various data visualisations later
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

# Run function to create duplicate dataframe containing percentage changes versus preceding quarter.
df_GDP_QvPriorQ = create_percentage_change_df(df_GDP, 1)

# Run function to create duplicate dataframe containing percentage changes versus the quarter in the previous year.
df_GDP_QvPriorY = create_percentage_change_df(df_GDP, 3)

# -------------------------------------------------------------------------------

# Create duplicate df that takes absolute values of each top-level GDP component, for usage in subsequent visualisation.
df_GDPComponents_Abs = abs(df_GDP[GDP_Components])
row_sums = df_GDPComponents_Abs.sum(axis=1)
df_GDPComponents_Abs = df_GDPComponents_Abs.div(row_sums, axis=0) * 100
# Note: the resulting dataframe calculates what proportion of the total absolute GDP values each component contributes.

# -------------------------------------------------------------------------------
# Create and tweak a duplicate dataframe to feed a "treemap" later. A bit tricky.
# -------------------------------------------------------------------------------

# Select the most recent row
recent_row = df_GDP.iloc[-1]

# identify the columns that are critical for building the treemap
columns_to_include = ["Household_Component_Durables", "Household_Component_SemiDurables", "Household_Component_NonDurables", 
                      "Household_Component_Services", "Household_Component_Other", "GDP_Component_Gov_Spend", 
                      "GDP_Component_GFCF", "GDP_Component_Inventories", "GDP_Component_TradeBalance", 
                      "GDP_Component_Other"]

# Create a DataFrame with one row containing the values from the most recent row
df_treemap = pd.DataFrame(recent_row[columns_to_include]).reset_index()

# Rename columns for brevity/clarity
df_treemap.columns = ['Component', 'Value']

# Treemap's cannot accept negative values - therefore we must ensure all values are positive
df_treemap["Value"] = abs(df_treemap["Value"])

# Create a new column (parent_component); this serves as the top-level hierarchy for the treemap.
# Please look at an example treemap to grasp the concept of hierarchy.
df_treemap["Parent_Component"] = df_treemap["Component"]

# Set the appropriate values for Parent_Component column.
# For example, the top-level hierarchy for "Household_Durables" is "Household_Spend".
mapping = {
    "Household_Component_Durables": "Household_Spend",
    "Household_Component_SemiDurables": "Household_Spend",
    "Household_Component_NonDurables": "Household_Spend",
    "Household_Component_Services": "Household_Spend",
    "Household_Component_Other": "Household_Spend",
    "GDP_Component_Gov_Spend": "Non_Household_Spend",
    "GDP_Component_GFCF": "Non_Household_Spend",
    "GDP_Component_Inventories": "Non_Household_Spend",
    "GDP_Component_TradeBalance": "Non_Household_Spend",
    "GDP_Component_Other": "Non_Household_Spend"}
df_treemap["Parent_Component"] = df_treemap["Parent_Component"].replace(mapping)

# The following values must be removed from "Parent_Component", to improve the aesthetics of the eventual treemap.
values_to_remove = ['GDP_Component_Gov_Spend', 'GDP_Component_GFCF', 
                    'GDP_Component_Inventories', 'GDP_Component_TradeBalance',
                    'GDP_Component_Other']
df_treemap['Parent_Component'] = df_treemap['Parent_Component'].replace(values_to_remove, '')

# Introduce line breaks in the Component column - to  improve the aesthetics of the eventual treemap.
df_treemap['Component'] = df_treemap['Component'].str.replace('_', '<br>')

# -------------------------------------------------------------------------------
# Manually define the bundle of dataframes and lists to "pickle", to feed the dashboard.
# -------------------------------------------------------------------------------

data_bundle = {
    'df_GDP': df_GDP,
    'df_GDP_QvPriorY': df_GDP_QvPriorY,
    'df_GDP_QvPriorQ': df_GDP_QvPriorQ,
    'df_GDPComponents_Abs': df_GDPComponents_Abs,
    'Household_Components': Household_Components,
    'GDP_Components': GDP_Components,
    'df_treemap': df_treemap}

# Save the bundle-dictionary to a pickle file
with open('data_bundle.pickle', 'wb') as f:
    pickle.dump(data_bundle, f)
    print("Data bundle saved successfully.")
# This pickle file will subsequently be fed through to the dashboard script ("BOE_Dash.py")

