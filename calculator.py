# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc
from dash.dependencies import Input, Output
from payments import Mortgage

app = Dash(__name__,   external_stylesheets=["https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css"],
                    external_scripts=["https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/js/bootstrap.bundle.min.js"])

app.layout = html.Div([
    html.Div(children=[
        html.Label('Property price:', style={'padding':'10px','font-weight':'bold','width':'15%'}, htmlFor='price'),
        dcc.Input(id='price',value=1200000,placeholder='price', type='number',  className='form-control-sm', style={'width':'15%'}),
        html.Label('Deposit:',  style={'padding':'10px', 'font-weight':'bold','width':'15%'}, htmlFor='deposit',form='deposit'),
        dcc.Input(id='deposit', value=170000,placeholder='deposit', type='number', className='form-control-sm', style={'width':'15%'}),
        html.Label('Other costs', htmlFor='other', style={'padding':'10px','font-weight':'bold','width':'15%'}),
        dcc.Input(id='other', value=70000,placeholder='other', type='number', className='form-control-sm', style={'width':'15%'})],
        style={'padding': 10, 'display':'inline', 'flex-direction':'row', 'width':'800px'}),
    html.Br(),
    html.Div(children=[
        html.Label('Interest rate', style={'padding':'10px','font-weight':'bold', 'width':'15%'}),
        dcc.Input(id='interest', value=5, type='number',className='form-control-sm', style={'width':'15%'}),
        html.Label('Loan term', style={'padding':'10px','font-weight':'bold', 'width':'15%'}),
        dcc.Input(id='term',value=30, type='number',  className='form-control-sm', style={'width':'15%'}),
        html.Label('Extra monthly repayments', style={'padding':'10px','font-weight':'bold', 'width':'15%'}),
        dcc.Input(id='extra',value=1000, type='number',  className='form-control-sm', style={'width':'15%'})],
        style={'padding': 10, 'display':'inline', 'flex-direction':'row', 'width':'800px'}),
        html.Br(),
    html.Div(children= [
        html.Label('Expected growth rate', style={'padding':'10px','font-weight':'bold', 'width':'15%'}),
        dcc.Input(id='growth',value=5, type='number',  className='form-control-sm', style={'width':'15%'}),
        html.Label('Sell in years', style={'padding':'10px','font-weight':'bold', 'width':'15%'}),
        dcc.Input(id='years_hold', value=10, type='number',  className='form-control-sm', style={'width':'15%'}),
        html.Label('Average inflation ', style={'padding':'10px','font-weight':'bold', 'width':'15%'}),
        dcc.Input(id='inflation',value=5, type='number',  className='form-control-sm', style={'width':'15%'})],
        style={'padding': 10,  'display':'inline', 'flex-direction':'row', 'width':'800px'}),
    html.Br(),
    html.Div([
        html.Label('Rent if not buying', style={'padding':'10px','font-weight':'bold', 'width':'15%'}),
        dcc.Input(id='rent',value=600, type='number',  className='form-control-sm', style={'width':'15%'}),
        html.Label('Return of ETF fund', style={'padding':'10px','font-weight':'bold', 'width':'15%'}),
        dcc.Input(id='index',value=6, type='number',  className='form-control-sm', style={'width':'15%'}),
 

        ], style={'padding': 10,  'display':'inline', 'flex-direction':'row', 'width':'800px'}),
    html.Br(),
    html.Br(),
    html.Br(),
    html.H3('Profit/Loss Statement'),
    html.Div(id='output'),

], )

@app.callback(
    Output('output', 'children'),
    Input('price','value'),
    Input('deposit','value'),
    Input('other','value'),
    Input('interest','value'),
    Input('term','value'),
    Input('extra','value'),
    Input('growth','value'),
    Input('years_hold','value'),
    Input('inflation','value'),
    Input('rent','value'),
    Input('index','value'),

    )
def update_graph(price, deposit, other, interest, term, extra, growth, years_hold, inflation, rent, index):
    m = Mortgage(interest, term, price, deposit, other)
    out = m.pl_report(years_hold, growth, inflation, extra, rent, index)
    elems = [html.Ul(o) for o in out if len(o)>0 ]
    return html.Li(elems, className='list-group')
 
if __name__ == '__main__':
    app.run_server(debug=True)

