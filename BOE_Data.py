#!/usr/bin/env python
# coding: utf-8

# In[6]:


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

# Obtain list of sheet names ("tabs") from the source xlsx file.
file = "Dashboard dataset.xlsx"
sheet_names = pd.ExcelFile(file).sheet_names

# Fully load the first "tab" in to a suitably named pandas dataframe ("df_GDP").
# Note: manual inspection of the xlsx file indicates the column headers begin at row index 4.
df_GDP = pd.read_excel(file, 
                       sheet_name = sheet_names[0], 
                       header = 4)

# Manually amend the column names for brevity.
column_mapping = {'Households: Final consumption expenditure': 'Household_Spend', 
                  'General Government: Final consumption expenditure': 'Gov_Spend',
                  'Gross fixed capital formation: Gross capital formation': 'GrossFixed_CapitalFormation',
                  'Changes in inventories: Gross capital formation': 'Changes_Inventories_GCF',
                  'Trade balance ': 'Trade_Balance',
                  'Other': 'GDP_Other',
                  'Gross domestic product at market prices': 'GDP_MarketPrices'}
df_GDP = df_GDP.rename(columns=column_mapping)

                  
# Fully load the next "tab" in to a temporary dataframe.
df_temp = pd.read_excel(file, 
                       sheet_name = sheet_names[1], 
                       header = 4)

# Manually amend the column names for brevity.
column_mapping = {'Total: UK National': 'Duplicate_Col',
                  'Durable goods: UK Domestic': 'Household_Durables',
                  'Semi-durable goods: UK Domestic': 'Household_SemiDurables',
                  'Non-durable goods: UK Domestic': 'Household_NonDurables',
                  'Services: UK Domestic': 'Household_Services',
                  'Other': 'Household_Other'}
df_temp = df_temp.rename(columns=column_mapping)
df_temp = df_temp.drop(columns="Duplicate_Col")

# The "time period" column shall be the index for each dataframe.
df_GDP.set_index('Time period and dataset code row', inplace=True)
df_temp.set_index('Time period and dataset code row', inplace=True)

# Combine the two df, and call the resulting df "df_GDP" (again)
df_GDP = pd.concat([df_GDP, df_temp], axis=1)
clean_index_name = "GDP_TimePeriod"
df_GDP.index.name = clean_index_name

# -------------------------------------------------------------------------------
# Tidy the resulting, combined dataframe
# -------------------------------------------------------------------------------

# Slice off a single, superfluous row from the resulting dataframe.
df_GDP = df_GDP[1:]

# Convert the format of the index to be truly recognised by Python as "datetime".
df_GDP.index = df_GDP.index.str.replace(' ', '-')
df_GDP.index = pd.to_datetime(df_GDP.index)

# Set datatype for all columns to floating (and deal with blank cells in the process)
df_GDP = df_GDP.apply(pd.to_numeric, errors='coerce').astype(float)

# -------------------------------------------------------------------------------
# Identify and define significant groupings of columns in the dataframe
# -------------------------------------------------------------------------------

# Define a list of the columns that represent top level *components* of GDP.
GDP_Components = list(df_GDP.columns)[:6]

# Define a list of the columns that represent *components* of Household Spending.
Household_Components = list(df_GDP.columns)[-5:]

# -------------------------------------------------------------------------------
# Create and tweak duplicate dataframes, to feed various data visualisations later
# -------------------------------------------------------------------------------

# Create duplicate dataframe containing percentage changes versus preceding quarter.
df_GDP_QvPriorQ = df_GDP.copy()
df_GDP_QvPriorQ = ((df_GDP_QvPriorQ / df_GDP_QvPriorQ.shift(1))-1)*100
df_GDP_QvPriorQ = df_GDP_QvPriorQ.astype(float)
df_GDP_QvPriorQ['Zscore'] = zscore(df_GDP_QvPriorQ['GDP_MarketPrices'], nan_policy='omit')
df_GDP_QvPriorQ['Zscore'] = np.clip(df_GDP_QvPriorQ['Zscore'], -4, 4)
# Note: Z-score is computed for the total GDP column, for usage in subsequent visualisations.
# Note: Z-score values are "clipped" to maximum +4, minimum -4.

# Create duplicate dataframe containing percentage changes versus the quarter in the previous year.
df_GDP_QvPriorY = df_GDP.copy()
df_GDP_QvPriorY = ((df_GDP_QvPriorY / df_GDP_QvPriorY.shift(3))-1)*100
df_GDP_QvPriorY = df_GDP_QvPriorY.astype(float)
df_GDP_QvPriorY['Zscore'] = zscore(df_GDP_QvPriorY['GDP_MarketPrices'], nan_policy='omit')
df_GDP_QvPriorY['Zscore'] = np.clip(df_GDP_QvPriorY['Zscore'], -4, 4)
# Note: Z-score is computed for the total GDP column, for usage in subsequent visualisations.
# Note: Z-score values are "clipped" to maximum +4, minimum -4.

# Create duplicate df that takes absolute values of each top-level GDP component, for usage in subsequent visualisation.
df_GDPComponents_Abs = abs(df_GDP[GDP_Components])
row_sums = df_GDPComponents_Abs.sum(axis=1)
df_GDPComponents_Abs = df_GDPComponents_Abs.div(row_sums, axis=0) * 100
# Note: the resulting dataframe calculations what proportion of the absolute GDP values each component contributes.

# -------------------------------------------------------------------------------
# Create and tweak a duplicate dataframe to feed a "treemap" later. A bit tricky.
# -------------------------------------------------------------------------------

# Select the most recent row
recent_row = df_GDP.iloc[-1]

# Filter the columns you want to include in the treemap
columns_to_include = ["Household_Durables", "Household_SemiDurables", "Household_NonDurables", "Household_Services", "Household_Other",
                      "Gov_Spend", "GrossFixed_CapitalFormation", "Changes_Inventories_GCF", "Trade_Balance", "GDP_Other"]

# Create a DataFrame with one row containing the values from the most recent row
df_treemap = pd.DataFrame(recent_row[columns_to_include]).reset_index()

# Rename columns
df_treemap.columns = ['Component', 'Value']

df_treemap["Value"] = abs(df_treemap["Value"])

df_treemap["Parent_Component"] = df_treemap["Component"]

# Define the mapping of values to be replaced
mapping = {
    "Household_Durables": "Household_Spend",
    "Household_SemiDurables": "Household_Spend",
    "Household_NonDurables": "Household_Spend",
    "Household_Services": "Household_Spend",
    "Household_Other": "Household_Spend",
    "Gov_Spend": "Non_Household_Spend",
    "GrossFixed_CapitalFormation": "Non_Household_Spend",
    "Changes_Inventories_GCF": "Non_Household_Spend",
    "Trade_Balance": "Non_Household_Spend",
    "GDP_Other": "Non_Household_Spend"
}

# Replace values in the "Parent_Component" column
df_treemap["Parent_Component"] = df_treemap["Parent_Component"].replace(mapping)

# Define the values to remove
values_to_remove = ['Gov_Spend', 'GrossFixed_CapitalFormation', 
                    'Changes_Inventories_GCF', 'Trade_Balance',
                    'GDP_Other']

# Replace the values with blanks
df_treemap['Parent_Component'] = df_treemap['Parent_Component'].replace(values_to_remove, '')

# Introduce line breaks in the Component column
df_treemap['Component'] = df_treemap['Component'].str.replace('_', '<br>')

# -------------------------------------------------------------------------------
# Save the bundle of dataframes and lists that will feed the dashboard
# -------------------------------------------------------------------------------

# Create a dictionary to bundle your DataFrames and lists
data_bundle = {
    'df_GDP': df_GDP,
    'df_GDP_QvPriorY': df_GDP_QvPriorY,
    'df_GDP_QvPriorQ': df_GDP_QvPriorQ,
    'df_GDPComponents_Abs': df_GDPComponents_Abs,
    'Household_Components': Household_Components,
    'GDP_Components': GDP_Components,
    'df_treemap': df_treemap
}

# Save the dictionary to a pickle file
with open('data_bundle.pickle', 'wb') as f:
    pickle.dump(data_bundle, f)

