import pandas as pd
from plotly import express as px

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from datetime import datetime
from datetime import date

import numpy as np

# import data
df = pd.read_excel("data/daylio.xlsx", sheet_name="data")
moods = pd.read_excel("data/daylio.xlsx", sheet_name="moods")

# clean data
df["full_date"] = pd.to_datetime(df["full_date"])

# average mood over time
aggregations = {"mood value": "mean"}
df_avgmood = df.groupby(by=["full_date", "name"])\
    .agg(aggregations)\
    .reset_index()\
    .rename(columns={'mood value': 'average mood'})


# variance of average mood over time between all members of the "name" class
aggregations = {"average mood": np.var}
df_mood_variance = df_avgmood.groupby("full_date")\
    .agg(aggregations)\
    .reset_index()\
    .rename(columns={'average mood': 'mood variance'})

# ------------------------------------------------------------------------
# Initialise App
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Daylio", style={"text-align": "center"}),

    dcc.DatePickerRange(
        id='my-date-picker-range',
        min_date_allowed=min(df["full_date"]),
        max_date_allowed=max(df["full_date"]),
        initial_visible_month=date(
            datetime.now().year, datetime.now().month, 1),
        start_date=min(df["full_date"]),
        end_date=max(df["full_date"]),
        display_format='DD MMM YYYY',
    ),

    html.Div(id='output-container-date-picker-range'),

    dcc.Graph(id="average-mood-over-time", figure={}),

    dcc.Graph(id="mood-variance-over-time", figure={}),
])

# ------------------------------------------------------------------------


@app.callback(
    Output(component_id="average-mood-over-time", component_property="figure"),
    [Input(component_id="my-date-picker-range", component_property="start_date"),
     Input(component_id="my-date-picker-range", component_property="end_date")]
)
def update_chart1(start_date, end_date):
    # print(start_date, type(start_date))
    # print(end_date, type(end_date))

    data_copy = df_avgmood.copy()
    data_copy = data_copy[(data_copy["full_date"] >= start_date) & (
        data_copy["full_date"] <= end_date)]

    figure = px.line(data_copy, x="full_date", y="average mood", color='name')

    figure.update_layout(legend=dict(
        yanchor="bottom",
        y=0.80,
        xanchor="left",
        x=0.01
    ))

    figure.layout.template = 'simple_white'

    return figure


@app.callback(
    Output(component_id="mood-variance-over-time",
           component_property="figure"),
    [Input(component_id="my-date-picker-range", component_property="start_date"),
     Input(component_id="my-date-picker-range", component_property="end_date")]
)
def update_chart2(start_date, end_date):
    data_copy = df_mood_variance.copy()
    data_copy = data_copy[(data_copy["full_date"] >= start_date) & (
        data_copy["full_date"] <= end_date)]

    figure = px.line(data_copy, x="full_date", y="mood variance")
    figure.layout.template = 'simple_white'
    return figure


# ------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
