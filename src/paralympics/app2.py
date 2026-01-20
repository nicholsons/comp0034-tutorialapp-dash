# Imports for dash, Dash.html and Dash bootstrap components (dbc)
import dash
import dash_bootstrap_components as dbc
from dash import html

# Create an instance of the Dash app, define the viewport meta tag and the external stylesheet
app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)

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
        {"label": "How have the number of sports, events, counties, participants changed?",
         "value": "line"},
        {"label": "How has the number of male and female participants changed?", "value": "bar"},
        {"label": "Where have the paralympics been hosted?", "value": "map"},
    ],
)

line_select = dbc.Select(
    id="line-select",
    options=[
        {"label": "Sports", "value": "sports"},
        {"label": "Events", "value": "events"},
        {"label": "Counties", "value": "counties"},
        {"label": "Participants", "value": "participants"},
    ],
)

barchart_checklist = html.Div(
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
        dbc.Col(html.Div(children=[
            chart_select,
            line_select,
            barchart_checklist,
        ], id="selectors"), width=4),
        dbc.Col(html.Div("Charts"), width=8),
    ]
)

row_two = dbc.Row(
    [
        dbc.Col(html.Div("Questions will go here")),
    ]
)

lead = html.P("Use the charts to explore the data and answer the questions below.", className="lead", id="intro")

# Add an HTML layout to the Dash app
# Start the layout with a Bootstrap container
app.layout = dbc.Container(children=[
    # Add the layout components in here
    navbar,
    lead,
    row_one,
    row_two,
], fluid=True)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
