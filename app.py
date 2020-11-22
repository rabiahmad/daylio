import pandas as pd
from plotly import express as px

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from datetime import datetime
from datetime import date


# import data
df = pd.read_excel("daylio.xlsx", sheet_name="data")
moods = pd.read_excel("daylio.xlsx", sheet_name="moods")

# clean data
df["full_date"] = pd.to_datetime(df["full_date"])

# aggregate data
aggregations = {"mood value": "mean"}
df_avgmood = df.groupby(by=["full_date", "name"]).agg(
    aggregations).reset_index()


# ------------------------------------------------------------------------
# Initialise App
external_stylesheets = ['https://codepen.io/anon/pen/mardKv.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

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

    dcc.Graph(id="average-mood-over-time", figure={})
])

# ------------------------------------------------------------------------


@app.callback(
    Output(component_id="average-mood-over-time", component_property="figure"),
    [Input(component_id="my-date-picker-range", component_property="start_date"),
     Input(component_id="my-date-picker-range", component_property="end_date")]
)
def update_chart(start_date, end_date):
    # print(start_date, type(start_date))
    # print(end_date, type(end_date))

    df_avgmood_copy = df_avgmood.copy()
    df_avgmood_copy = df_avgmood_copy[(df_avgmood_copy["full_date"] >= start_date) & (
        df_avgmood_copy["full_date"] <= end_date)]

    figure = px.line(df_avgmood_copy, x="full_date",
                     y="mood value", color='name')
    return figure


# ------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
