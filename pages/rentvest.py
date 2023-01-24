from dash import Dash, html, dcc, dash_table, callback
from dash.dependencies import Input, Output
from payments import Mortgage
import dash
import pandas as pd


layout = html.Div(
    [
        html.Div(
            children=[
                html.Label(
                    "Property price:",
                    style={"padding": "10px", "font-weight": "bold", "width": "15%"},
                    htmlFor="price",
                ),
                dcc.Input(
                    id="price-rentvest",
                    value=1200000,
                    placeholder="price",
                    type="number",
                    className="form-control-sm",
                    style={"width": "15%"},
                ),
                html.Label(
                    "Deposit:",
                    style={"padding": "10px", "font-weight": "bold", "width": "15%"},
                    htmlFor="deposit",
                    form="deposit",
                ),
                dcc.Input(
                    id="deposit-rentvest",
                    value=170000,
                    placeholder="deposit",
                    type="number",
                    className="form-control-sm",
                    style={"width": "15%"},
                ),
                html.Label(
                    "Other costs",
                    htmlFor="other",
                    style={"padding": "10px", "font-weight": "bold", "width": "15%"},
                ),
                dcc.Input(
                    id="other-rentvest",
                    value=70000,
                    placeholder="other",
                    type="number",
                    className="form-control-sm",
                    style={"width": "15%"},
                ),
            ],
            style={
                "padding": 10,
                "display": "inline",
                "flex-direction": "row",
                "width": "800px",
            },
        ),
        html.Br(),
        html.Div(
            children=[
                html.Label(
                    "Interest rate",
                    style={"padding": "10px", "font-weight": "bold", "width": "15%"},
                ),
                dcc.Input(
                    id="interest-rentvest",
                    value=5,
                    type="number",
                    className="form-control-sm",
                    style={"width": "15%"},
                ),
                html.Label(
                    "Loan term",
                    style={"padding": "10px", "font-weight": "bold", "width": "15%"},
                ),
                dcc.Input(
                    id="term-rentvest",
                    value=30,
                    type="number",
                    className="form-control-sm",
                    style={"width": "15%"},
                ),
                html.Label(
                    "Interest only",
                    style={"padding": "10px", "font-weight": "bold", "width": "15%"},
                ),
                dcc.RadioItems(
                    options=["Yes", "No"],
                    value="Yes",
                    id="interest-only-rentvest",
                    className="form-control-sm",
                    style={"width": "15%", "margin": "1px"},
                    inline=False,
                ),
            ],
            style={
                "padding": 10,
                "display": "inline",
                "flex-direction": "row",
                "width": "800px",
            },
        ),
        html.Br(),
        html.Div(
            children=[
                html.Label(
                    "Expected growth rate",
                    style={"padding": "10px", "font-weight": "bold", "width": "15%"},
                ),
                dcc.Input(
                    id="growth-rentvest",
                    value=5,
                    type="number",
                    className="form-control-sm",
                    style={"width": "15%"},
                ),
                html.Label(
                    "Sell in years",
                    style={"padding": "10px", "font-weight": "bold", "width": "15%"},
                ),
                dcc.Input(
                    id="years_hold-rentvest",
                    value=10,
                    type="number",
                    className="form-control-sm",
                    style={"width": "15%"},
                ),
                html.Label(
                    "Average inflation ",
                    style={"padding": "10px", "font-weight": "bold", "width": "15%"},
                ),
                dcc.Input(
                    id="inflation-rentvest",
                    value=5,
                    type="number",
                    className="form-control-sm",
                    style={"width": "15%"},
                ),
            ],
            style={
                "padding": 10,
                "display": "inline",
                "flex-direction": "row",
                "width": "800px",
            },
        ),
        html.Br(),
        html.Div(
            [
                html.Label(
                    "Rent",
                    style={"padding": "10px", "font-weight": "bold", "width": "15%"},
                ),
                dcc.Input(
                    id="rent-rentvest",
                    value=600,
                    type="number",
                    className="form-control-sm",
                    style={"width": "15%"},
                ),
                html.Label(
                    "Extra monthly cost",
                    style={"padding": "10px", "font-weight": "bold", "width": "15%"},
                ),
                dcc.Input(
                    id="monthly-cost-rentvest",
                    value=0,
                    type="number",
                    className="form-control-sm",
                    style={"width": "15%"},
                ),
          html.Label(
                    "Personal Rent",
                    style={"padding": "10px", "font-weight": "bold", "width": "15%"},
                ),
                dcc.Input(
                    id="personal-rent-rentvest",
                    value=0,
                    type="number",
                    className="form-control-sm",
                    style={"width": "15%"},
                ),

            ],
            style={
                "padding": 10,
                "display": "inline",
                "flex-direction": "row",
                "width": "800px",
            },
        ),
        html.Br(),
        html.Br(),
        html.Br(),
        html.H3("Profit/Loss Statement"),
        # html.Div(id='output'),
        dash_table.DataTable(
            id="dtable-rentvest",
            columns=[
                {"name": "Description", "id": "Description"},
                {"name": "Value", "id": "Value"},
            ],
            style_cell={"text-align": "center"},
        ),
    ],
)


@callback(
    Output("dtable-rentvest", "data"),
    Input("price-rentvest", "value"),
    Input("deposit-rentvest", "value"),
    Input("other-rentvest", "value"),
    Input("interest-rentvest", "value"),
    Input("term-rentvest", "value"),
    Input("interest-only-rentvest", "value"),
    Input("growth-rentvest", "value"),
    Input("years_hold-rentvest", "value"),
    Input("inflation-rentvest", "value"),
    Input("rent-rentvest", "value"),
    Input("monthly-cost-rentvest", "value"),
    Input("personal-rent-rentvest", "value"),

)
def update_graph(
    price,
    deposit,
    other,
    interest,
    term,
    interest_only,
    growth,
    years_hold,
    inflation,
    rent,
    monthly_cost,
    personal_rent
):
    m = Mortgage(interest, term, price, deposit, other)
    out = m.pl_report_rentvest(
        years_hold, growth, inflation, monthly_cost, interest_only, rent, personal_rent
    )
    out = [o.strip() for o in out if len(o.strip()) > 0]
    # elems = [html.Ul(o) for o in out if len(o)>0 ]
    elems = {
        "Description": [x.split(":")[0] for x in out],
        "Value": [x.split(":")[1] for x in out],
    }
    df = pd.DataFrame(elems)
    print(df)
    # dt = dash_table.DataTable(df.to_dict('records'), [{"name": i, "id": i} for i in df.columns])
    return df.to_dict("records")
    # return html.Li(elems, className='list-group')
