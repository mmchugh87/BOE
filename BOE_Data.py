#!/usr/bin/env python
# coding: utf-8

# In[99]:


# -------------------------------------------------------------------------------
# Import additional Python functionality / various libraries
# -------------------------------------------------------------------------------

import pandas as pd
import numpy as np
from scipy.stats import zscore
import pickle

# -------------------------------------------------------------------------------
# Import additional functions from our own BOE_Utilities module
# -------------------------------------------------------------------------------

import BOE_Utilities

# -------------------------------------------------------------------------------
# Use BOE_Utilities to create a fully combined and transformed dataframe
# -------------------------------------------------------------------------------

# Run a chain of BOE_Utilities functions together on the source file
file_name = 'Dashboard dataset.xlsx'

# Based on a manual review of the source files, define alternative column names for brevity / clarity
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

# Define and then execute a chain of functions from our BOE_Utilities module.
# This chain of functions receives the xlsx file and the column_mapping, and then combines and transforms the xlsx data...
#...into a dataframe that will subsequently be used to generate other useful dataframes and plots.
def create_df_gdp(file_name, column_mapping):
    df = create_combined_dataframe(file_name)
    df = tidy_the_dataframe(df)
    df = rename_columns(df, column_mapping)
    return df
    
# Run the chain of functions and assign the resulting dataframe
df_GDP = create_df_gdp(file_name=file_name, column_mapping=column_mapping)

# -------------------------------------------------------------------------------
# Manually identify meaningful groupings of columns (used in subsequent plots)
# -------------------------------------------------------------------------------

# Define a list of the columns that are the top-level *components* of GDP.
GDP_Components = list(df_GDP.columns)[:6]
# This list will be used later, when creating plots

# Define a list of the columns that are the top-level *components* of Household Spend.
Household_Components = list(df_GDP.columns)[-5:]
# This list will be used later, when creating plots

# -------------------------------------------------------------------------------
# Use BOE_Utilities to create duplicate dataframes containing % change values (used in subsequent plots)
# -------------------------------------------------------------------------------

# Run function to create duplicate dataframe containing percentage changes versus preceding quarter.
df_GDP_QvPriorQ = create_percentage_change_df(df_GDP, 1)

# Run function to create duplicate dataframe containing percentage changes versus the quarter in the previous year.
df_GDP_QvPriorY = create_percentage_change_df(df_GDP, 4)

# -------------------------------------------------------------------------------
# Create a duplicate df containing absolute values of GDP components (used in subsequent plots)
# -------------------------------------------------------------------------------

df_GDPComponents_Abs = abs(df_GDP[GDP_Components])
row_sums = df_GDPComponents_Abs.sum(axis=1)
df_GDPComponents_Abs = df_GDPComponents_Abs.div(row_sums, axis=0) * 100
# Note: the resulting dataframe calculates what proportion of the total absolute GDP values each component contributes.

# -------------------------------------------------------------------------------
# Create and tweak a duplicate dataframe to feed a "treemap" (used in subsequent plots)
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
# Bundle the dataframes and lists created above, and "pickle" them. This bundle will feed the dashboard.
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

