import pandas as pd
from plotly import express as px

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from datetime import datetime
from datetime import date


from scipy import signal

# import data
df = pd.read_excel("daylio.xlsx", sheet_name="data")
moods = pd.read_excel("daylio.xlsx", sheet_name="moods")

df["full_date"] = pd.to_datetime(df["full_date"])

# aggregate data
aggregations = {"mood value": "mean"}
df_avgmood = df.groupby(by=["full_date", "name"]).agg(
    aggregations).reset_index()

print(df_avgmood)
print(type(df_avgmood["full_date"]))


fig = px.line(df_avgmood, x="full_date", y="mood value", color='name')
# fig.show()


# ------------------------------------------------------------------------
# Initialise App
app = dash.Dash(__name__)


app.layout = html.Div([
    html.H1("Daylio", style={"text-align": "center"}),

    dcc.DatePickerRange(
        id='my-date-picker-range',
        min_date_allowed=date(2020, 1, 1),
        max_date_allowed=date(2020, 12, 1),
        initial_visible_month=date(2020, 8, 1),
        end_date=date(2020, 12, 1)
    ),

    html.Div(id='output-container-date-picker-range'),

    dcc.Graph(id="average-mood-over-time", figure=fig)
])

app.run_server(debug=True)
# ------------------------------------------------------------------------
