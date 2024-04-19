# UK GDP Dashboard
##### Coding Assignment April 2024

### Introduction
The goal of this GitHub repository is to generate an interactive dashboard, with which to monitor the evolution over time of UK GDP and some of its key components.

The dashboard is generated from a python script ("BOE_Dash.py") and makes heavy use of python libraries "Dash" and "Plotly".
The live dashboard can be accessed online, here:

**https://mmchugh87-github-io.onrender.com/**

(Note: this dashboard is rendered via a free online service called "render.com". It is a free service and as such, the page can be slow to load. In some cases it may become necessary to "refresh" the page - please be patient with it).

### Dashboard Workflow

* **Step 1: Data Source** ("Dashboard dataset.xlsx") - the data source must be located within the same folder (or GitHub repository) as the following python scripts.
* **Step 2: Load & Transform Data Source** ("BOE_Data.py") - this python script uses pandas library to load, clean and transform the Data Source from step 1. The final output of this python script is an object called "data_bundle.pickle", which contains several dataframes that feed in to subsequent data visualisations.
* **Step 3: Load data_bundle and generate interactive dashboard** ("BOE_Dash.py") - this python script unpacks the "data_bundle.pickle" object produced in step 2, and uses the resulting bundle of dataframes to generate various plots. This python script makes heavy use of "Dash" and "Plotly" libraries to build the dashboard and its interactive features.
