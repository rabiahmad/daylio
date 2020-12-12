# importing the required libraries
import pandas as pd
import numpy as np
import re
from plotly import express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import datetime
from datetime import date
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
import time


# ------------------------------------------------------------------------
# Initialise App
app = dash.Dash(__name__)
server = app.server
# ------------------------------------------------------------------------


# setting up the Google Sheets API variables and credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = 'creds.json'

credentials = None
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)


# import data
SAMPLE_SPREADSHEET_ID = '1TNe_T7JwdpEqBenb0_6t6aHXJqaSlyJ1IrTyl7vR3BY'
SAMPLE_RANGE_NAME_HIBAH = 'Hibah!A1:G10000'
SAMPLE_RANGE_NAME_RABI = 'Rabi!A1:G10000'
service = build('sheets', 'v4', credentials=credentials)
sheet = service.spreadsheets()


# clean data
def get_date(string):
    regex = '^(\d{2})\/(\d{2})\/(\d{4})$'
    m = re.match(regex, string)
    dateparts = (m.group(3), m.group(2), m.group(1))
    sep = '-'
    date = sep.join(dateparts)
    return date


def get_dataframe():
    '''Use this to periodically refresh the dataframe'''
    result_h = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                  range=SAMPLE_RANGE_NAME_HIBAH).execute()
    values_h = result_h.get('values')

    result_r = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                  range=SAMPLE_RANGE_NAME_RABI).execute()
    values_r = result_r.get('values')

    values = values_r + values_h[1:]

    df = pd.DataFrame(values[1:], columns=values[0])
    df['full_date'] = df['full_date'].apply(lambda d: get_date(d))
    df['mood value'] = df['mood value'].astype(str).astype(int)
    return df


df = get_dataframe()

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

    dcc.Graph(id="avg_mood_range_over_time", figure={}),

    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # in milliseconds
        n_intervals=0
    )

])

# ------------------------------------------------------------------------


def get_average_mood_over_time(df=get_dataframe()):
    '''Get average mood over time dataframe'''
    aggregations = {"mood value": "mean"}
    df_avgmood = df.groupby(by=["full_date", "name"])\
        .agg(aggregations)\
        .reset_index()\
        .rename(columns={'mood value': 'average mood'})
    return df_avgmood


def get_mood_variance_over_time(df=get_average_mood_over_time()):
    '''Get average mood variance over time dataframe'''
    aggregations = {"average mood": np.var}
    df_mood_variance = df.groupby("full_date")\
        .agg(aggregations)\
        .reset_index()\
        .rename(columns={'average mood': 'mood variance'})
    return df_mood_variance


def get_mood_range_over_time(df=get_dataframe()):
    '''Get average mood range over time.
    logic: get the max(mood) - min(mood) per day. Then calculate moving average using all previous values. Do this BY name.'''

    df_avgrange = df.groupby(by=["full_date", "name"])\
        .agg(max_mood=("mood value", np.max), min_mood=("mood value", np.min))\
        .reset_index()\

    df_avgrange["mood_range"] = df_avgrange.apply(
        lambda x: x["max_mood"] - x["min_mood"], axis=1)

    df_avgrange = df_avgrange.set_index("full_date").groupby(
        "name").expanding(min_periods=1).mean().reset_index()
    return df_avgrange
# ------------------------------------------------------------------------


@app.callback(
    Output(component_id="average-mood-over-time", component_property="figure"),
    [
        Input(component_id="my-date-picker-range",
              component_property="start_date"),
        Input(component_id="my-date-picker-range",
              component_property="end_date"),
        Input('interval-component', 'n_intervals')
    ]
)
def update_chart1(start_date, end_date, _):
    '''Periodically update the average mood over time graph'''
    time.sleep(2)
    data_copy = get_average_mood_over_time(df=get_dataframe())
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
    [
        Input(component_id="my-date-picker-range",
              component_property="start_date"),
        Input(component_id="my-date-picker-range",
              component_property="end_date"),
        Input('interval-component', 'n_intervals')
    ]
)
def update_chart2(start_date, end_date, _):
    '''Periodically update the average mood variance over time graph'''
    time.sleep(4)
    df = get_average_mood_over_time(df=get_dataframe())
    data_copy = get_mood_variance_over_time(df=df)
    data_copy = data_copy[(data_copy["full_date"] >= start_date) & (
        data_copy["full_date"] <= end_date)]

    figure = px.line(data_copy, x="full_date", y="mood variance")
    figure.layout.template = 'simple_white'
    return figure


@app.callback(
    Output(component_id="avg_mood_range_over_time",
           component_property="figure"),
    [
        Input(component_id="my-date-picker-range",
              component_property="start_date"),
        Input(component_id="my-date-picker-range",
              component_property="end_date"),
        Input('interval-component', 'n_intervals')
    ]
)
def update_chart3(start_date, end_date, _):
    time.sleep(6)
    data_copy = get_mood_range_over_time(df=get_dataframe())
    data_copy = data_copy[(data_copy["full_date"] >= start_date) & (
        data_copy["full_date"] <= end_date)]

    figure = px.line(data_copy, x="full_date", y="mood_range", color="name")
    figure.layout.template = 'simple_white'
    return figure


# ------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
