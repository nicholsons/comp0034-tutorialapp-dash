# Imports for dash, Dash.html and Dash bootstrap components (dbc)
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html

from paralympics import charts

# Create an instance of the Dash app
app = dash.Dash(
    prevent_initial_callbacks="initial_duplicate",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)

# Prevents issues where callbacks rely on an id that is not present in the layout when the app runs
app.config.suppress_callback_exceptions = True

# Defining the layout elements as variables can make the code easier to read and restructure
navbar = dbc.Navbar(children=[
    dbc.Container(children=[
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(html.Img(src=app.get_asset_url("mono-logo.webp"), height="40px")),
                    # dbc components use class_name=
                    dbc.Col(dbc.NavbarBrand("Paralympics research app", class_name="navbar-brand")),
                ],
                align="center",
            ),
            href="#",
            style={"textDecoration": "none"},
        ),
    ],
        fluid=True
    ),
],
    color="black",
    dark=True,
)

chart_select = dbc.Select(
    id='select-chart',
    options=[
        {"label": "How have the number of sports, events, countries, participants changed?",
         "value": "line"},
        {"label": "How has the number of male and female participants changed?", "value": "bar"},
        {"label": "Where have the paralympics been hosted?", "value": "map"},
    ],
    placeholder="Choose the question you want to explore",
)


def create_linechart_select():
    """ Returns a select box to choose the feature for the line chart"""
    return dbc.Select(
        id="line-select",
        options=[
            {"label": "Sports", "value": "sports"},
            {"label": "Events", "value": "events"},
            {"label": "Countries", "value": "countries"},
            {"label": "Participants", "value": "participants"},
        ],
        placeholder="Choose a feature to display",
    )


def create_barchart_checklist():
    """ Returns a checklist box to choose the type of Paralympics for the bar chart """
    return html.Div(
        [
            dbc.Label("Choose one or both options"),
            dbc.Checklist(
                options=[
                    {"label": "Winter", "value": "winter"},
                    {"label": "Summer", "value": "summer"},
                ],
                value=[],
                id="checklist-barchart",
                inline=True,
            ),
        ]
    )


row_one = dbc.Row(
    [
        dbc.Col(children=[
            chart_select,  # The initial selector to choose the chart, this is always present
            html.Div(children=[], id="selectors")
            # A div to add the extra selectors dependent on chart-type
        ], width=4),
        dbc.Col(html.Div("Charts", id="chart-display"), width=8),
    ]
)

row_two = dbc.Row(
    [
        dbc.Col(html.Div("Questions will go here")),
    ]
)

lead = html.P("Use the charts to explore the data and answer the questions below.",
              className="lead", id="intro")

# Add an HTML layout to the Dash app
# Start the layout with a Bootstrap container
app.layout = dbc.Container(children=[
    # Add the layout components in here
    navbar,
    lead,
    row_one,
    row_two,
], fluid=True)


# Callbacks
@app.callback(
    Output("chart-display", "children", allow_duplicate=True),
    Output("selectors", "children"),
    Input("select-chart", "value"),
)
def update_chart_display(chart_type):
    """ Updates the chart display and selectors based on the selected chart-type

    Args:
        chart_type (str): one of "line", "map", "bar" else empty

    Returns:
        graphs (list), selectors (list): graphs is a list of chart components, selectors is a list of selectors

        NB The order of the variables returned matches the order of the Outputs in the callback decorator
    """
    if not chart_type:
        raise dash.exceptions.PreventUpdate

    selectors = []
    graphs = []

    if chart_type == "line":
        line_select = create_linechart_select()
        selectors.append(line_select)
    elif chart_type == "bar":
        barchart_checklist = create_barchart_checklist()
        selectors.append(barchart_checklist)
    elif chart_type == "map":
        figure = charts.scatter_map()
        graphs.append(dcc.Graph(figure=figure, id="scatter-map"))
    else:
        raise dash.exceptions.PreventUpdate

    return graphs, selectors


@app.callback(
    Output("chart-display", "children", allow_duplicate=True),
    [Input("line-select", "value")],
)
def display_line_chart(selected_value):
    """ Takes the selected feature and displays the line chart """
    if not selected_value:
        raise dash.exceptions.PreventUpdate

    graph = dcc.Graph(figure=charts.line_chart(selected_value),
                      id=f"{selected_value}-chart")
    return graph


@app.callback(
    Output("chart-display", "children"),
    [Input("checklist-barchart", "value")],
)
def display_bar_chart(event_types):
    """ Takes the selected Paralympics type(s) and displays the bar chart(s)

    Args:
        event_types (List[str]): one or both of 'winter', 'summer'

    Returns:
        graphs (list): List of chart components
    """
    if not event_types:
        raise dash.exceptions.PreventUpdate

    graphs = []

    for event_type in event_types:
        graph = dcc.Graph(figure=charts.bar_chart(event_type),
                          id=f"{event_type}-barchart")
        graphs.append(graph)

    return graphs


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
