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
import sys
import json

conn = sqlite3.connect("housing.db")
city = sys.argv[1]
query = '''SELECT * FROM suburb_performance_{}_Years'''.format(city)
df = pd.read_sql_query(query, conn)
df['DATE'] = pd.to_datetime(df[['year', 'month']].assign(DAY=1))
query = '''SELECT * FROM suburb_demographic_{}'''.format(city)
df_demo = pd.read_sql_query(query,conn)
suburbs = list(set(df['suburb'].to_list()))
cats = df_demo['category'].unique()
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
types = ["Unit", "House"]
beds = [1,2,3,4,5]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

filters = ['state','suburb','postcode','type','bedrooms']
available_indicators = df.columns.to_list()
available_indicators = list(set(available_indicators)-set(filters))

#Get geojson of NSW
with open('../nsw.geojson','r') as f:
    subs = json.load(f)

#Get data only for relevant suburbs
suburbs_rel = suburbs.copy()
subs_geo = {}
subs_geo['features']=[]
for row in subs['features']:
    if(row['properties']['nsw_loca_2'].title() in suburbs_rel):
        row['id'] = row['properties']['nsw_loca_2'].title()
        subs_geo['features'].append(row)
        suburbs_rel.remove(row['id'])
    if(len(suburbs_rel)==0):
        break
subs_geo['type']= 'FeatureCollection'

app.layout = html.Div([

    html.Div([
            html.Div([
            dcc.Dropdown(
                id='filt',
                options=[{'label': i, 'value': i} for i in suburbs],
                value=['Kingsford','Randwick'], multi=True
            )],
            style={'display': 'inline-block', 'width':'33%'}),

            html.Div([
            dcc.Dropdown(
                id='filt2',
                options=[{'label': i, 'value': i} for i in types],
                value='Unit'
            )],
            style={'display': 'inline-block', 'width':'33%'}),

            html.Div([
            dcc.Dropdown(
                id='filt3',
                options=[{'label': i, 'value': i} for i in beds],
                value=[2], multi=True
            )],
            style={'display': 'inline-block', 'width':'33%'}),

        html.Div([
            dcc.Dropdown(
                id='xaxis-column',
                options=[{'label': i, 'value': i} for i in available_indicators],
                value='DATE'
            ),
        ],
        style={'display': 'inline-block', 'width':'49%'}),

        html.Div([
            dcc.Dropdown(
                id='yaxis-column',
                options=[{'label': i, 'value': i} for i in available_indicators],
                value=['lowestSoldPrice','medianSoldPrice'], multi=True
            ),
        ],
        style={'display': 'inline-block', 'width':'49%'})
    ]),

    dcc.Graph(id='indicator-graphic'),

    html.Div([html.H2("Demographic")]),
    html.Div([
         dcc.Dropdown(
                id='subs',
                options=[{'label': i, 'value': i} for i in suburbs],
                value='Kingsford', multi=False
            ),
    dcc.Dropdown(
       id='var',
       options=[{'label': i, 'value': i} for i in cats],
       value='CountryOfBirth', multi=False
   ),
   dcc.Graph(id='pie-chart')],
    style={'width':'49%', 'display': 'inline-block'}),

   html.Div([
         dcc.Dropdown(
                id='subs1',
                options=[{'label': i, 'value': i} for i in suburbs],
                value='Randwick', multi=False
            ),
    dcc.Dropdown(
       id='var1',
       options=[{'label': i, 'value': i} for i in cats],
       value='CountryOfBirth', multi=False
   ),
    dcc.Graph(id='pie-chart2')],
   style={'width':'49%', 'display': 'inline-block','float':'right'}),

    html.Div([html.H2("Map")]),
   html.Div([
        html.P('Data based on 2021'),

        html.Div([
         dcc.Dropdown(
                id='ind',
                options=[{'label': i, 'value': i} for i in available_indicators],
                value='medianSoldPrice', multi=False
            ),
         ], style={'width':'33%','display':'inline-block'}),

        html.Div([
         dcc.Dropdown(
                id='ind2',
                options=[{'label': i, 'value': i} for i in types],
                value='House', multi=False
            ),
         ], style={'width':'33%','display':'inline-block'}),

        html.Div([
         dcc.Dropdown(
                id='ind3',
                options=[{'label': i, 'value': i} for i in beds],
                value=2, multi=False
            ),
         ], style={'width':'33%','display':'inline-block'}),


    html.Div([html.Br()]),
    dcc.Graph(id='map-plot')],

   style={'width':'90%', 'display': 'inline-block','float':'left'}),
   html.Br(),
   html.Br(),


])

@app.callback(
    Output('indicator-graphic', 'figure'),
    Input('filt','value'),
    Input('filt2','value'),
    Input('filt3','value'),
    Input('xaxis-column', 'value'),
    Input('yaxis-column', 'value'))
def update_graph(filt,filt2,filt3,xaxis_column_name, yaxis_column_name):
    dff = df.loc[df['suburb'].isin(filt)]
    dff = dff.loc[dff['bedrooms'].isin(filt3)]
    dff = dff[dff['type']==filt2]
    sList = filt.copy()
    fig = px.line(dff,x=xaxis_column_name,y=yaxis_column_name[0],color="bedrooms",line_dash="suburb",\
            labels = {"bedrooms":"Beds", "suburb":"Suburb"})
    sList = yaxis_column_name.copy()
    del sList[0]
    for var in sList:
        fig2 = px.line(dff,x=xaxis_column_name,y=var,color="bedrooms",line_dash="suburb").update_traces(mode="lines+markers")
        for i in range(len(fig2.data)):
            fig.add_trace(fig2.data[i])

    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')
    fig.update_layout(legend=dict(
    yanchor="top",
    y=0.99,
    xanchor="left",
    x=0.01
))

    return fig

@app.callback(
    Output('pie-chart', 'figure'),
    Input('subs','value'),
    Input('var','value'))
def dummy_pie_chart(*args,**kwargs):
    return generate_pie_chart(*args,**kwargs)

def generate_pie_chart(subs, var):
    dff = df_demo[df_demo['suburb']==subs]
    dff = dff[dff['category']==var]
    total = dff['value'].sum()
    dff = dff.nlargest(5,'value')
    other = total-dff['value'].sum()
    if(other>0):
        dff.reset_index(inplace=True, drop=True)      
        dff.loc[dff.shape[0]] = dff.loc[dff.shape[0]-1] 
        dff.loc[dff.shape[0]-1,'subcategory']  = 'Other'   # To display correct proportions in pie chart
        dff.loc[dff.shape[0]-1,'value'] = other
    fig = px.pie(dff,values='value',names='subcategory', labels={'subcategory':var})
    fig.update_traces(textinfo='percent+label',textposition='inside')
    fig.update_layout(legend=dict(
        yanchor="bottom",
        y=1.0,
        xanchor="left",
        x=0.0,
        font=dict(size=10),
        orientation='h'))
    return fig

@app.callback(
    Output('pie-chart2', 'figure'),
    Input('subs1','value'),
    Input('var1','value'))
def dummy_pie_chart2(*args, **kwargs):
    return generate_pie_chart(*args, **kwargs)

@app.callback(
        Output('map-plot', 'figure'),
        Input('ind','value'),
        Input('ind2','value'),
        Input('ind3','value'))
def get_map_plot(ind,ind2,ind3):
    #get latest data for each suburb
    #df_map = df.sort_values('DATE').groupby('suburb').tail(1)
    #print(df_map.medianSoldPrice.info())
    df_map = df[(df['year']==2022) & (df['month']==4) & (df['bedrooms']==ind3) & (df['type']==ind2)]
    df_map = df_map[ (df_map['bedrooms']==ind3) & (df_map['type']==ind2)]
    df_map = df_map[~df_map[ind].isna()]
    fig = px.choropleth_mapbox(df_map, geojson=subs_geo, locations='suburb', color=ind,
                           color_continuous_scale="Viridis",
                           #range_color=(0, 1e5),
                           mapbox_style="carto-positron",
                           zoom=10, 
                           center = {"lat": -33.8893, "lon": 151.092},
                           opacity=0.3,
                           #labels={'unemp':'unemployment rate'}
                          )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

