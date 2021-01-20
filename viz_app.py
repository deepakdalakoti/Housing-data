import sqlite3
import pandas as pd
import numpy as np

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
conn = sqlite3.connect("housing.db")
query = '''SELECT * FROM suburb_performance_yearly'''
df = pd.read_sql_query(query, conn)
#df['DATE'] = pd.to_datetime(df[['year', 'month']].assign(DAY=1))
suburbs = list(set(df['suburb'].to_list()))
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
types = ["Unit", "House"]
beds = [1,2,3]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

#df = pd.read_csv('https://plotly.github.io/datasets/country_indicators.csv')
#print(df)
filters = ['state','suburb','postcode','type','bedrooms']
available_indicators = df.columns.to_list()
available_indicators = list(set(available_indicators)-set(filters))
#print(available_indicators)

app.layout = html.Div([

    html.Div([
            html.Div([
            dcc.Dropdown(
                id='filt',
                options=[{'label': i, 'value': i} for i in suburbs],
                value=['Kingsford','Randwick'], multi=True
            )]),
        #style={'width': '30%', 'display': 'inline-block'}),

            html.Div([
            dcc.Dropdown(
                id='filt2',
                options=[{'label': i, 'value': i} for i in types],
                value='Unit'
            )]),
        #style={'width': '30%', 'display': 'inline-block'}),

            #html.Div([
            #dcc.Dropdown(
            #    id='filt3',
            #    options=[{'label': i, 'value': i} for i in beds],
            #    value=1
            #)]),
        #style={'width': '30%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                id='xaxis-column',
                options=[{'label': i, 'value': i} for i in available_indicators],
                value='year'
            ),
        ]),
        #style={'width': '30%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                id='yaxis-column',
                options=[{'label': i, 'value': i} for i in available_indicators],
                value=['lowestSoldPrice','medianSoldPrice'], multi=True
            ),
        ])
        #,style={'width': '30%', 'float': 'right', 'display': 'inline-block'})
    ]),

    dcc.Graph(id='indicator-graphic'),

    #dcc.Slider(
    #    id='year--slider',
    #    min=df['Year'].min(),
    #    max=df['Year'].max(),
    #    value=df['Year'].max(),
    #    marks={str(year): str(year) for year in df['Year'].unique()},
    #    step=None
    #)
])

@app.callback(
    Output('indicator-graphic', 'figure'),
    Input('filt','value'),
    Input('filt2','value'),
    #Input('filt3','value'),
    Input('xaxis-column', 'value'),
    Input('yaxis-column', 'value'))
    #Input('year--slider', 'value'))
def update_graph(filt,filt2,xaxis_column_name, yaxis_column_name):
    #dff = df[df['Year'] == year_value]
    dff = df.loc[df['suburb'].isin(filt)]
    dff = dff[dff['type']==filt2]
    #dff = dff[dff['bedrooms']==filt3]
    #fig = px.scatter(x=dff[xaxis_column_name],
    #                 y=dff[yaxis_column_name],color="bedrooms")
    #fig = go.Figure()
    #fig.add_trace(go.Scatter(dff,x=xaxis_column_name,y=yaxis_column_name,color="bedrooms",
    #    mode='lines', name = 'suburb'))
    sList = filt.copy()
    #print(type(filt))
    #df2 = dff[dff['suburb']==filt[0]]
    fig = px.line(dff,x=xaxis_column_name,y=yaxis_column_name[0],color="bedrooms",line_dash="suburb",\
            labels = {"bedrooms":"Beds", "suburb":"Suburb"})
    sList = yaxis_column_name.copy()
    del sList[0]
    for var in sList:
        print(var)
    #    df2 = dff[dff['suburb']==sub]
    #    #print(df2)
        fig2 = px.line(dff,x=xaxis_column_name,y=var,color="bedrooms",line_dash="suburb").update_traces(mode="lines+markers")
        for i in range(len(fig2.data)):
            fig.add_trace(fig2.data[i])
        #fig.add_trace(fig2.data[1])
        #fig.add_trace(fig2.data[2])
    #    fig.add_trace(fig2.data[1])

    #    fig.add_trace(go.Scatter(x=dff[xaxis_column_name], y=dff[var], mode="lines+markers"))

                     #hover_name=dff[dff['Indicator Name'] == yaxis_column_name]['Country Name'])

    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')
    fig.update_layout(legend=dict(
    yanchor="top",
    y=0.99,
    xanchor="left",
    x=0.01
))

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

#print(df)
