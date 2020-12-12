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
SAMPLE_RANGE_NAME = 'data!A1:G335'
service = build('sheets', 'v4', credentials=credentials)
sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=SAMPLE_RANGE_NAME).execute()
values = result.get('values')
df = pd.DataFrame(values[1:], columns=values[0])

# clean data


def convert_str_to_date(input, input_format, output_format='%Y-%m-%d'):
    '''Convert date string dd/mm/yyyy to datetime yyyy-mm-dd using regular expressions'''
    date = pd.datetime.strptime(str(input), input_format)
    return date  # date.strftime(output_format)


def get_date(string):
    regex = '^(\d{2})\/(\d{2})\/(\d{4})$'
    m = re.match(regex, string)
    dateparts = (m.group(3), m.group(2), m.group(1))
    sep = '-'
    date = sep.join(dateparts)
    return date


# df["full_date"] = pd.to_datetime(df["full_date"])

df['full_date'] = df['full_date'].apply(lambda d: get_date(d))


print(df["full_date"].unique())

# df["full_date"] = df["full_date"]\
#     .apply(lambda x: convert_str_to_date(x, input_format='%Y-%d-%m'))

df['mood value'] = df['mood value'].astype(str).astype(int)

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


# average daily range over time between all members of the "name" class
# logic: get the max(mood) - min(mood) per day. Then calculate moving average using all previous values. Do this BY name.
df_avgrange = df.groupby(by=["full_date", "name"])\
    .agg(max_mood=("mood value", np.max), min_mood=("mood value", np.min))\
    .reset_index()\

df_avgrange["mood_range"] = df_avgrange.apply(
    lambda x: x["max_mood"] - x["min_mood"], axis=1)


df_avgrange = df_avgrange.set_index("full_date").groupby(
    "name").expanding(min_periods=1).mean().reset_index()


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

    dcc.Graph(id="avg_mood_range_over_time", figure={})

])

# ------------------------------------------------------------------------


@app.callback(
    Output(component_id="average-mood-over-time", component_property="figure"),
    [Input(component_id="my-date-picker-range", component_property="start_date"),
     Input(component_id="my-date-picker-range", component_property="end_date")]
)
def update_chart1(start_date, end_date):

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


@app.callback(
    Output(component_id="avg_mood_range_over_time",
           component_property="figure"),
    [Input(component_id="my-date-picker-range", component_property="start_date"),
     Input(component_id="my-date-picker-range", component_property="end_date")]
)
def update_chart3(start_date, end_date):
    data_copy = df_avgrange.copy()
    data_copy = data_copy[(data_copy["full_date"] >= start_date) & (
        data_copy["full_date"] <= end_date)]

    figure = px.line(data_copy, x="full_date", y="mood_range", color="name")
    figure.layout.template = 'simple_white'
    return figure


# ------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
