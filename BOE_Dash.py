#!/usr/bin/env python
# coding: utf-8

# In[62]:


# -------------------------------------------------------------------------------
# Import additional Python functionality / various libraries
# -------------------------------------------------------------------------------

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pickle
from scipy.stats import zscore
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import Dash, html, dash_table, dcc, callback, Output, Input

# -------------------------------------------------------------------------------
# Load the bundle of dataframes and lists to be used in this dashboard
# -------------------------------------------------------------------------------

# Load the dictionary bundle that was created in the "BOE_Data.py" script.
with open('data_bundle.pickle', 'rb') as f:
    loaded_data_bundle = pickle.load(f)

# Access the individual DataFrames or lists from the loaded dictionary bundle
df_GDP = loaded_data_bundle['df_GDP']
df_GDP_QvPriorY = loaded_data_bundle['df_GDP_QvPriorY']
df_GDP_QvPriorQ = loaded_data_bundle['df_GDP_QvPriorQ']
df_GDPComponents_Abs = loaded_data_bundle['df_GDPComponents_Abs']
Household_Components = loaded_data_bundle['Household_Components']
GDP_Components = loaded_data_bundle['GDP_Components']
df_treemap = loaded_data_bundle['df_treemap']

# -------------------------------------------------------------------------------
# Initialize our interactive dashboard app
# -------------------------------------------------------------------------------

# Standard code to initialise dash dashboard (using a "dbc" style theme)
app = dash.Dash(external_stylesheets=[dbc.themes.PULSE])
app.title = "UK GDP Dashboard"
# This line is required for the dashboard to successfully render online via render.com
server = app.server

# -------------------------------------------------------------------------------
# Define Dashboard Components (Dashboard Position: Row 1 of 5, Col 1 of 3)
# -------------------------------------------------------------------------------

# Defint the text for a Markdown component in the dashboard
markdown_text = """
### UK GDP Dashboard
###### Note: Not optimised for small screens.
This interactive tool provides a high-level overview of GDP growth rates, and the evolution over time of the major components of GDP and UK Household consumption.
"""

# Define the RadioItems buttons, for user to change % Quarter Comparison
radio_display = dcc.RadioItems(
    id='radio-display',
    options=[
        {'label': 'Current Quarter vs Prior Quarter', 'value': 'prior_q'},
        {'label': 'Current Quarter vs Same Quarter Last Year', 'value': 'prior_y'}
        ],
    value='prior_q', # when dashboard first loads, this is the value automatically selected
    labelStyle={'display': 'block'}
    )

# -------------------------------------------------------------------------------
# Define Dashboard Components (Dashboard Position: Row 1 of 5, Col 2 of 3)
# -------------------------------------------------------------------------------

# Define callback to update the plot based on selected radio button value
@app.callback(
    Output('Plot_GDP_Heatmap', 'figure'),
    Input('radio-display', 'value')
    )

def update_heatmap(selected_option):
    # Slice the DataFrame based on the selected radio button value
    if selected_option == 'prior_q':
        sliced_df = df_GDP_QvPriorQ.iloc[-10:, :7]
        title = "% Change For Various GDP Components.<br>Current Quarter vs Prior Quarter"
    else:
        sliced_df = df_GDP_QvPriorY.iloc[-10:, :7]
        title = "% Change For Various GDP Components.<br>Current Quarter vs Same Quarter Last Year"
    
    # Transpose and format the DataFrame
    sliced_df_transposed = sliced_df.transpose()
    sliced_df_transposed.columns = pd.to_datetime(sliced_df_transposed.columns)
    sliced_df_transposed.columns = sliced_df_transposed.columns.to_period('Q').strftime('%Y Q%q')
    sliced_df_transposed = round(sliced_df_transposed, 2)
    
    # Create the heatmap
    fig_heatmap = px.imshow(
        sliced_df_transposed,
        color_continuous_scale='ice',
        range_color=[-1000, 50],
        text_auto=True,
        aspect='auto',
        title=title
        )
    
    fig_heatmap.update_layout(
        xaxis_title=None,
        coloraxis={'showscale': False},
        title_x=0.5,
        title_y=0.9
        )
    
    fig_heatmap.update_traces(textfont=dict(size=11))
    
    return fig_heatmap

Plot_GDP_Heatmap = dcc.Graph(id='Plot_GDP_Heatmap')

# -------------------------------------------------------------------------------
# Define Dashboard Components (Dashboard Position: Row 1 of 5, Col 3 of 3)
# -------------------------------------------------------------------------------

# Define the number of bins for the histogram
num_bins = 100  # Adjust as needed

# Create the numpy array
bars_array = np.arange(-4.1, 4.2, 0.1)

# Define the callback to update the histogram based on the radio_display selection
@app.callback(
    Output('Plot_GDP_histogram', 'figure'),
    [Input('radio-display', 'value')]
    )

def update_histogram(selected_radio):
    if selected_radio == 'prior_q':
        df = df_GDP_QvPriorQ
        title = "Histogram of GDP growth rates as Zscores.<br>The most recent growth rate is highlighted yellow.<br>Current Quarter versus Prior Quarter."

    elif selected_radio == 'prior_y':
        df = df_GDP_QvPriorY
        title = "Histogram of GDP growth rates as Zscores.<br>The most recent growth rate is highlighted yellow.<br>Current Quarter versus Same Quarter Last Year."

    # Create a histogram trace for the Z-score distribution
    hist_trace = go.Histogram(
        x=df['Zscore'].dropna(),
        name='Zscore',
        opacity=1,
        xbins=dict(size=0.1),
        autobinx=False,
        marker=dict(line=dict(width=0.25, color='black'))
        )

    # Find the index position in the array
    bar_to_highlight = df['Zscore'].iloc[-1]
    bar_position = np.abs(bars_array - bar_to_highlight).argmin() - 1
    colors = ['yellow' if i == bar_position else 'steelblue' for i in range(num_bins)]

    # Update marker color based on highlighted bar
    hist_trace.marker.color = colors

    # Define the layout for the histogram
    hist_layout = go.Layout(
        title=title,
        xaxis=dict(title='Zscore (Note: extreme Z-scores are capped at +/- 4.0)'),
        yaxis=dict(title='Frequency'),
        bargap=0.2,
        bargroupgap=0.1,
        title_x=0.5,
        title_y=0.9
        )

    # Combine the trace and layout into a figure
    hist_figure = go.Figure(data=[hist_trace], layout=hist_layout)

    return hist_figure

# Create the plot object
Plot_GDP_histogram = dcc.Graph(id='Plot_GDP_histogram')

# -------------------------------------------------------------------------------
# Define Dashboard Components (Dashboard Position: Row 2 of 5, Col 1 of 2)
# -------------------------------------------------------------------------------

# Define some useful objects, to enable the user to set what timeframe for the plots to display data for.
min_year_in_dataset = min(df_GDP_QvPriorQ.index.year)
max_year_in_dataset = max(df_GDP_QvPriorQ.index.year)
default_year = str(1990)

# Define the start year dropdown, for the user to set what timeframe for the plots to display data for
start_year_dropdown = dcc.Dropdown(
    id='start-year-dropdown',
    options=[{'label': str(year), 'value': year} for year in range(min_year_in_dataset, max_year_in_dataset+1)],
    value=default_year, # when dashboard first loads, this is the value automatically selected
    placeholder='Select starting year',
    clearable=False
    )

# Define the end year dropdown, for the user to set what timeframe for the plots to display data for
end_year_dropdown = dcc.Dropdown(
    id='end-year-dropdown',
    options=[{'label': str(year), 'value': year} for year in range(min_year_in_dataset, max_year_in_dataset+1)],
    value=max_year_in_dataset,  # when dashboard first loads, this is the value automatically selected
    placeholder='Select ending year',
    clearable=False
    )

# Define the RadioItems buttons, for the user to select what TYPE of plot to display
radio_plot_type = dcc.RadioItems(
    id='radio-plot-type',
    options=[
        {'label': 'Bar Plot', 'value': 'bar'},
        {'label': 'Line Plot', 'value': 'line'}
        ],
    value='bar',  # when dashboard first loads, this is the value automatically selected
    labelStyle={'display': 'block'}
    )

# Define the RadioItems buttons, for the user to change how the dashboard treats outliers
radio_outlier_handling = dcc.RadioItems(
    id='radio-outlier-handling',
    options=[
        {'label': 'Include Outliers', 'value': 'include'},
        {'label': 'Dampen Outliers', 'value': 'dampen'}
        ],
    value='include',  # when dashboard first loads, this is the value automatically selected
    labelStyle={'display': 'block'}
    )

# -------------------------------------------------------------------------------
# Define Dashboard Components (Dashboard Position: Row 2 of 5, Col 2 of 2)
# -------------------------------------------------------------------------------

# Define the callback to update the y-axis range and time range based on user selections
@app.callback(
    Output('Plot_GDP_Time', 'figure'),
    [Input('radio-display', 'value'),
     Input('radio-plot-type', 'value'),
     Input('radio-outlier-handling', 'value'),
     Input('start-year-dropdown', 'value'),
     Input('end-year-dropdown', 'value')]
    )

def update_gdp_time_plot(selected_option, plot_type, outlier_handling, start_year, end_year):
    # Convert start year and end year to strings
    start_year_str = str(start_year)
    end_year_str = str(end_year)
    
    # Choose the appropriate DataFrame based on the selected option
    if selected_option == 'prior_q':
        df = df_GDP_QvPriorQ.loc[start_year_str:end_year_str]
        title = 'GDP % Change.<br>Current Quarter vs Prior Quarter'
    elif selected_option == 'prior_y':
        df = df_GDP_QvPriorY.loc[start_year_str:end_year_str]
        title = 'GDP % Change.<br>Current Quarter vs Same Quarter Last Year'
    
    y_data = df['GDP_MarketPrices']
    
    if plot_type == 'bar':
        trace = go.Bar(
            x=df.index,
            y=y_data,
            name='GDP at market prices (£m)',
            marker=dict(line=dict(width=0.25, color='black')),)
    elif plot_type == 'line':
        trace = go.Scatter(
            x=df.index,
            y=y_data,
            mode='lines',
            name='GDP at market prices (£m)')
    
    # Set y-axis range based on outlier handling option
    if outlier_handling == 'include':
        y_range = [-25, 25]
    elif outlier_handling == 'dampen':
        y_range = [-5, 5]
    
    layout = go.Layout(
        title=title,
        yaxis={'title': 'GDP at market prices (£m)', 'range': y_range},
        bargap=0.2
        )
    
    return {'data': [trace], 'layout': layout}

# Create the plot object
Plot_GDP_Time = dcc.Graph(id='Plot_GDP_Time')

# -------------------------------------------------------------------------------
# Define Dashboard Components (Dashboard Position: Row 3 of 5, Col 1 of 2)
# -------------------------------------------------------------------------------

# Define the color scheme dropdown selector
color_scheme_dropdown = dcc.Dropdown(
    id='color-scheme-dropdown',
    options=[
        {'label': 'Primary', 'value': 'Primary'},
        {'label': 'Nature', 'value': 'Nature'},
        {'label': 'Mono', 'value': 'Mono'}
        ],
    value='Nature',  # when dashboard first loads, this is the value automatically selected
    clearable=False,  # Ensure the dropdown has a value and is not clearable
    searchable=False,  # Disable search functionality
    placeholder="Select Color Scheme"
    )

markdown_text2="""
*Note: the percentages in this stacked bar chart are calculated on the basis of the **absolute** values of each GDP component.
Occasionally some of these components have a **negative** impact on GDP.
This plot provides an indication for the relative importance of each component as a driver for GDP growth or contraction*
"""

# -------------------------------------------------------------------------------
# Define Dashboard Components (Dashboard Position: Row 3 of 5, Col 2 of 2)
# -------------------------------------------------------------------------------

# Define the callback to update the stacked bar chart based on start and end year selections
@app.callback(
    Output('Plot_GDP_Stacks', 'figure'),
    [Input('start-year-dropdown', 'value'),
     Input('end-year-dropdown', 'value'),
     Input('color-scheme-dropdown', 'value')]
    )

def update_stacked_bar_chart(start_year, end_year, color_scheme):
    # Convert start year and end year to strings
    start_year_str = str(start_year)
    end_year_str = str(end_year)
    
    # Slice the DataFrame based on the selected start and end years
    sliced_df = df_GDPComponents_Abs.loc[start_year_str:end_year_str, GDP_Components]

    # Define color schemes
    color_schemes = {
        'Primary': ['royalblue', 'orange', 'green', 'red', 'yellow', 'purple'],
        'Nature': ['rosybrown', 'wheat', 'peru', 'olive', 'skyblue', 'seagreen'],
        'Mono': ['darkgray', 'whitesmoke', 'silver', 'gainsboro', 'slategray', 'black']
        }
    
    trace_colors = color_schemes[color_scheme]

    bar_traces = []
    for i, column in enumerate(sliced_df.columns):
        bar_trace = go.Bar(
            x=sliced_df.index,
            y=sliced_df[column],
            name=column,
            marker=dict(color=trace_colors[i], line=dict(width=0.25, color='black')),
            )
        bar_traces.append(bar_trace)

    # Configure the stacked bar chart layout
    bar_layout = go.Layout(
        title='Charting The Changing Significance Of GDP Components, To Total GDP',
        title_x=0.5,
        yaxis={'title': 'Percentage', 'range': [0, 100]},
        barmode='stack',
        bargap=0,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.02,
            xanchor="left",
            x=0.005))

    # Combine the "bar_traces" and "layout" objects into a fully defined stacked bar chart
    bar_figure = go.Figure(data=bar_traces, layout=bar_layout)

    return bar_figure

# Create the plot object
Plot_GDP_Stacks = dcc.Graph(id='Plot_GDP_Stacks')

# -------------------------------------------------------------------------------
# Define Dashboard Components (Dashboard Position: Row 4 of 5, Col 1 of 2)
# -------------------------------------------------------------------------------

# Give user ability to select a specific GDP component for visualisation in the bar chart
dropdown_options = [{'label': col, 'value': col} for col in df_GDP_QvPriorQ[GDP_Components].columns]

Buttons_Components = dcc.Dropdown(
        id='Buttons_Components',
        options=dropdown_options,
        value=df_GDP_QvPriorQ[GDP_Components].columns[-2], # when dashboard first loads, this is the value automatically selected
        clearable=False)

markdown_text3="""
*Note: This chart does **not** display the percentage changes for GDP components. 
Some of these components are volatile and produce extreme percentage changes, meaning the **level** provides a more intuitive guide to the evolution of GDP.*
"""

# -------------------------------------------------------------------------------
# Define Dashboard Components (Dashboard Position: Row 4 of 5, Col 2 of 2)
# -------------------------------------------------------------------------------
    
@app.callback(
    Output('Plot_GDP_Components', 'figure'),
    [Input('Buttons_Components', 'value'),
     Input('start-year-dropdown', 'value'),
     Input('end-year-dropdown', 'value')]
    )

def update_bar_chart(selected_column, start_year, end_year):
    # Slice the DataFrame based on the selected time range
    start_year_str = str(start_year)
    end_year_str = str(end_year)
    df = df_GDP.loc[start_year_str:end_year_str]
    
    y_data = df[selected_column]
    
    # Create the trace with steelblue fill color and thin line border
    trace = go.Bar(
        x=df.index,
        y=y_data,
        name=selected_column,
        marker=dict(line=dict(width=0.25, color='black'))
        )
    
    layout = go.Layout(
        title=f'Bar Chart Showing The Changing Level Of {selected_column}',
        yaxis={'title': 'Level (£m)'}
        )
    
    return {'data': [trace], 'layout': layout}

# Create the plot object
Plot_GDP_Components = dcc.Graph(id='Plot_GDP_Components')

# -------------------------------------------------------------------------------
# Define Dashboard Components (Dashboard Position: Row 5 of 5, Col 1 of 3)
# -------------------------------------------------------------------------------

# Sort the columns ascending, highest value first.
# We do this to resolve a strange problem whereby the color of the lines changes, when the user changes which lines to display.
# We want the colors to be fixed, stable, consistent.
sorted_columns = df_GDP[Household_Components].iloc[-1].sort_values(ascending=False).index

# Define the checklist options
checklist_options = [{'label': component, 'value': component} for component in sorted_columns]

# Define the checklist component
checklist = dcc.Checklist(
    id='component-checkboxes',
    options=checklist_options,
    value=df_GDP[Household_Components].columns.tolist(),  # By default, select to display ALL components
    labelStyle={'display': 'block'}
    )

# -------------------------------------------------------------------------------
# Define Dashboard Components (Dashboard Position: Row 5 of 5, Col 2 of 3)
# -------------------------------------------------------------------------------

# Callback to update the line plot based on the selected components
@app.callback(
    Output('Plot_Household_Time', 'figure'),
    [Input('component-checkboxes', 'value')]
    )

def update_line_plot(selected_components):
    traces = []
    colors = ['blue', 'red', 'green', 'orange', 'purple']  # Define fixed colors for the lines
    
    for component in selected_components:
        color_index = df_GDP[Household_Components].columns.get_loc(component)
        color = colors[color_index % len(colors)]
        
        traces.append(go.Scatter(
            x=df_GDP.index[120:],  # Apply the slicing here
            y=df_GDP[component][120:],  # Apply the slicing here
            mode='lines',
            name=component,
            line=dict(color=color)
            ))

    # Define the slider steps
    slider_steps = [
        {'args': [None, {'frame': {'duration': 500, 'redraw': True}, 'fromcurrent': True, 'transition': {'duration': 300, 'easing': 'quadratic-in-out'}}],
         'label': 'Play',
         'method': 'animate'},
        {'args': [[None], {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate', 'transition': {'duration': 0}}],
         'label': 'Pause',
         'method': 'animate'}
        ]

    layout = go.Layout(
        xaxis={'range': [df_GDP.index[120], df_GDP.index[-1]]},  # Set initial range
        yaxis={'title': 'Level (£m)'},
        legend={'x': 0, 'y': 1.2, 'orientation': 'h'},  # Position the legend towards the top left
        margin={'l': 80, 'r': 50, 't': 50, 'b': 50},  # Add some margin to accommodate the legend
        showlegend=True,  # Enable legend display
        sliders=[{
            'currentvalue': {'visible': False},
            'steps': [{'label': '', 'method': 'relayout', 'args': [{'xaxis.range': [df_GDP.index[i], df_GDP.index[-1]]}]} for i in range(120, len(df_GDP.index), 10)],
            'pad': {'t': 50}  # Add padding to accommodate slider
            }]
            )
    
    return {'data': traces, 'layout': layout}

# Create the plot object for the line plot
Plot_Household_Time = dcc.Graph(id='Plot_Household_Time')

# -------------------------------------------------------------------------------
# Define Dashboard Components (Dashboard Position: Row 5 of 5, Col 3 of 3)
# -------------------------------------------------------------------------------

# The colors are manually defined here to match the colors of the adjacent line plot (in Col 2 of 3).
# It would be better to come up with a programmatic way of assigning colors in a stable, consistent way.
color_scheme = ["red", "steelblue", "green", "purple", "hotpink", 
                "steelblue", "blue", "steelblue", "steelblue", "orange",
                "black"]

# Create the treemap
fig_treemap = px.treemap(
    data_frame=df_treemap,
    path=["Parent_Component", "Component"],
    values="Value",
    color="Component",
    color_discrete_sequence=color_scheme,
    custom_data=[df_treemap["Component"]],  # Add the Component column as custom data
    )

# Set the title and center it
fig_treemap.update_layout(
    title='Treemap Showing The Relatve Sizes Of GDP Components.<br>(Using The Most Recent Quarter Values)',
    margin={'l': 45, 'r': 45, 't': 45, 'b': 45},
    title_x=0.5,
    title_y=0.95,
    )

# Add borders to the treemap blocks
for trace in fig_treemap.data:
    trace.marker.line.color = 'black'
    trace.marker.line.width = 0.5

# Create the plot object
Plot_Treemap = dcc.Graph(id='Plot_Treemap', figure=fig_treemap)

# -------------------------------------------------------------------------------
# Organise the Dashboard
# -------------------------------------------------------------------------------

# Define the app layout
app.layout = html.Div(children=[
    
    # Row 1
    html.Div(children=[
        # Column 1
        html.Div(
            [dcc.Markdown(markdown_text), 
             html.Div(html.Strong("Select Periodicity:")), 
             radio_display,],
            style={'width': '20%', 'height': '455px', 'border-right': '3px solid black', 
                   'border-bottom': '0.5px solid silver', "padding":"20px", 
                   'background-color': 'lavender'}
                    ),
        # Column 2
        html.Div(
            Plot_GDP_Heatmap, 
            style={'width': '40%', 'height': '455px', 'border-right': '0.5px solid silver',
                   'border-bottom': '0.5px solid silver'}
                    ),
        # Column 3
        html.Div(
            Plot_GDP_histogram,
            style={'width': '40%', 'height': '455px', 'border-bottom': '0.5px solid silver'}
            ),
            ], 
             style={'display': 'flex', 'height': '455px'}),
    
#-----------------------------------------------------------------------------------
    
    # Row 2
    html.Div(children=[

        # Column 1
        html.Div(
            [html.Div(html.Strong("Period Of Investigation:")), 
             start_year_dropdown, end_year_dropdown,
             html.Div(html.Strong("Select Plot Type:"), style={'margin-top': '10px'}), 
             radio_plot_type,
             html.Div(html.Strong("Combat Outliers?"), style={'margin-top': '10px'}), 
             radio_outlier_handling],
            style={'width': '20%', 'height': '455px', 'border-right': '3px solid black', 
                   'border-bottom': '0.5px solid silver', "padding":"20px", 
                   'background-color': 'lavender'}
                    ),
    
        # Column 2
        html.Div(Plot_GDP_Time, style={'width': '80%', 'height': '455px', 'border-bottom': '0.5px solid silver'}),
        ], 
        style={'display': 'flex', 'height': '455px'}),
    
#-----------------------------------------------------------------------------------
    
    # Row 3
    html.Div(children=[
        
        # Column 1
        html.Div(
            [html.Div(html.Strong("Color Scheme:")), 
             color_scheme_dropdown,
            dcc.Markdown(markdown_text2, style={'margin-top': '10px'})],
            style={'width': '20%', 'height': '455px', 'border-right': '3px solid black', 
                   'border-bottom': '0.5px solid silver', "padding":"20px", 
                   'background-color': 'lavender'}
                    ),

        # Column 2
        html.Div(Plot_GDP_Stacks, style={'width': '80%', 'height': '455px', 'border-bottom': '0.5px solid silver'}),
        ], 
        style={'display': 'flex', 'height': '455px'}),
    
#-----------------------------------------------------------------------------------
    
    # Row 4
    html.Div(children=[

        # Column 1
        html.Div(
            [html.Div(html.Strong("Select GDP Component:")), 
             Buttons_Components,
            dcc.Markdown(markdown_text3, style={'margin-top': '10px'})],
            style={'width': '20%', 'height': '455px', 'border-right': '3px solid black', 
                   'border-bottom': '0.5px solid silver', "padding":"20px", 
                   'background-color': 'lavender'}
                    ),
        
        # Column 2
        html.Div(Plot_GDP_Components, 
                 style={'width': '80%', 'height': '455px', 
                        'border-bottom': '0.5px solid silver'}
                        ),
                        ], 
             style={'display': 'flex', 'height': '455px'}),

#-----------------------------------------------------------------------------------
    
    # Row 5
    html.Div(children=[
        
        # Column 1
        html.Div(
            [html.Div(html.Strong("Select Household Components:")), 
             checklist,],
            style={'width': '20%', 'height': '455px', 'border-right': '3px solid black', 
                   'border-bottom': '0.5px solid silver', "padding":"20px", 
                   'background-color': 'lavender'}
                    ),
        
        # Column 2
        html.Div(
            Plot_Household_Time, 
            style={'width': '40%', 'height': '455px', 'border-right': '0.5px solid silver', 
                   'border-bottom': '0.5px solid silver'}
                    ),
        
        # Column 3
        html.Div(
            Plot_Treemap,
            style={'width': '40%', 'height': '455px', 'border-bottom': '0.5px solid silver'}
            ),
            ], 
             style={'display': 'flex', 'height': '455px'}),

            ])

# -------------------------------------------------------------------------------
# Execute the dashboard
# -------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run_server(debug=False)

