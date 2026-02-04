""" Note to students: at 400 lines this is not a good example of how to structure code for readability. """
from typing import List

import dash
import dash_bootstrap_components as dbc
import requests
from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

from paralympics import charts

API_BASE_URL = "http://127.0.0.1:8000/"

# --- APP INSTANCE AND CONFIG ---
app = dash.Dash(
    # prevent_initial_callbacks="initial_duplicate",
    prevent_initial_callbacks=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)

# Prevents issues where callbacks rely on an id that is not present in the layout when the app runs
app.config.suppress_callback_exceptions = True


# --- HELPER FUNCTIONS ---
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


def get_number_questions():
    """ Helper to get the number of questions available"""
    q_resp = requests.get(f"{API_BASE_URL}/question", timeout=2)
    q_resp.raise_for_status()
    questions = q_resp.json()
    return len(questions)


def get_question(qid: int):
    """ Helper to get the question"""
    q_resp = requests.get(f"{API_BASE_URL}/question/{qid}", timeout=2)
    q_resp.raise_for_status()
    q = q_resp.json()
    return q


def get_responses(qid: int):
    """ Helper to get the questions and responses for a given question id"""
    r_resp = requests.get(f"{API_BASE_URL}/response/search?question_id={qid}", timeout=2)
    r_resp.raise_for_status()
    r = r_resp.json()
    return r


def create_question(q: dict):
    """
    Constructs a list of Dash components for presenting a question and its possible responses,
    including a radio button group for response selection and a submit button.

    Args:
    q (dict): A dictionary containing details of the question such as its ID and text. Must have the keys:
              - "id" (str | int): A unique identifier for the question.
              - "question_text" (str): The question text to display.
    Returns:
         A list of Dash components, including:
             - A label for displaying the question text.
             - A hidden paragraph element containing the question ID.
             - A radio button group for selecting a response.
             - A line break element.
             - A submit button for submitting the response.
    """
    responses = get_responses(q["id"])
    options = [{"label": r.get("response_text", ""), "value": r.get("id")} for r in responses]
    radio = dbc.RadioItems(id="question-radio", options=options, value=None)
    submit_btn = dbc.Button("Submit answer", id="submit-btn", n_clicks=0, color="primary")
    return [
        html.Label(q.get("question_text", ""), id="question-label"),
        radio,
        html.Br(),
        submit_btn,
    ]


def add_responses_to_new_question(number) -> List[dbc.Row]:
    """ Helper function to add responses to a new question

    Args:
        number (int): The number of response options to generate

    Returns:
        rows (List[dbc.Row]): A list of dbc components to add to UI
        """
    rows = []
    for n in range(number):
        rows.append(
            dbc.Row([
                dbc.Col(dbc.Input(id=f"response_text_{n}", required=True)),
                dbc.Col(html.Div([
                    dbc.Checkbox(id=f"is_correct_{n}", label="Correct response?", value=False),
                    html.Br()
                ])
                ),
            ])
        )
    return rows


# --- LAYOUT ELEMENTS ---
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

row_one = dbc.Row(children=[
    dbc.Col(children=[
        html.H2("Charts"),
        chart_select,  # The initial selector to choose the chart, this is always present
        html.Div(children=[], id="selectors")
        # A div to add the extra selectors dependent on chart-type
    ], width=4),
    dbc.Col(html.Div("", id="chart-display"), width=8),
])

row_two = dbc.Row(children=[
    dbc.Col(children=[
        html.Hr(),
        html.H2("Questions"),
        # Store the question num. Start with 1.
        # storage_type="session" means the index persists per tab;
        # set to "memory" to reset on reload, or "local" to persist across tabs.
        dcc.Store(id="q_index", data=1, storage_type="session"),
        html.Div(id="question", children=create_question(get_question(1))),  # First question
        html.Br(),
        html.Div(id="result"),  # For messages/feedback
    ])
])

lead = html.P("Use the charts to explore the data and answer the questions below.",
              className="lead", id="intro")

question_form = html.Div(children=[
    html.H2("Create a question"),
    dbc.Form([dbc.Label("Question text"),
              dbc.Textarea(
                  id="question_text",
                  placeholder="Enter the question text",
                  style={"width": "100%"}
              ),
              html.Hr(),
              html.H5("Add the four potential responses, indicate which is correct"),
              html.Div(children=add_responses_to_new_question(4)),
              dbc.Button("Add question", id="new-question-submit-button", color="primary"),
              ])
])

# --- LAYOUT ---
app.layout = dbc.Container(children=[
    navbar,
    dbc.Tabs([
        dbc.Tab(label='Paralympics dashboard and questions', children=[
            lead,
            row_one,
            row_two
        ]),
        dbc.Tab(label='Teacher admin', children=[
            question_form,
            html.Div(id="form-message")
        ])
    ])
], fluid=True)


# --- CALLBACKS ---
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


@app.callback(
    Output("q_index", "data"),  # updated index (1-based)
    Output("result", "children"),  # feedback message
    Input("submit-btn", "n_clicks"),  # submit click
    State("q_index", "data"),  # current index
    State("question-radio", "value"),  # selected response id
    prevent_initial_call=True,  # avoid firing on load
)
def handle_submit(n_clicks, index, selected_response_id):
    """ Handles the question progress and any feedback message

    Args:
        n_clicks (int): if the button was clicked or not
        index (int): the index of the question from the dcc.Store
        selected_response_id (str): the response id

    Returns:
        q_index (int): the selected question id
        result (str): a feedback message
        """
    if not n_clicks:
        raise PreventUpdate

    # Require a selection
    if selected_response_id in (None, "", []):
        return index, [html.Div("Please select an answer.", className="alert alert-info")]

    # Evaluate answer
    try:
        responses = get_responses(index)
    except Exception as e:
        return index, [html.Div(f"Unable to load responses. {e}", className="alert alert-info")]

    selected = next(
        (r for r in responses if str(r.get("id")) == str(selected_response_id)),
        None,
    )

    # Get the number of questions
    try:
        num_q = get_number_questions()
    except Exception as e:
        return index, [html.Div(f"Unable to load questions. {e}", className="alert alert-danger")]

    if selected and selected.get("is_correct"):
        # Finish if last question
        if index >= num_q:
            return num_q, [
                html.Div("Questions complete, well done!", className="alert alert-success")]
        # Otherwise advance
        next_index = index + 1
        return next_index, ""
    else:
        # Incorrect: stay on the same index
        stay_index = index
        return stay_index, [html.Div("Please try again!", className="alert alert-info")]


@app.callback(
    Output("question", "children"),  # rendered question block
    Input("q_index", "data"),  # current index
    prevent_initial_call=True,  # don't run on load
)
def render_question(index):
    """ Takes the question id and renders the question component in the layout

    Args:
        index (int): the question id

    Returns:
        question (html.Div): the question component
        """
    if not index:
        raise PreventUpdate

    try:
        num_q = get_number_questions()
    except Exception as e:
        return [html.Div(f"Unable to load questions. {e}", className="alert alert-danger")]

    # If past the last question, clear the block
    if index > num_q:
        return []

    try:
        q = get_question(index)
    except Exception as e:
        return [html.Div(f"Unable to load question. {e}", className="alert alert-danger")]

    return create_question(q)


@app.callback(
    Output("form-message", "children"),
    Input("new-question-submit-button", "n_clicks"),
    State("question_text", "value"),
    # states for the 4 response text inputs
    [State(f"response_text_{i}", "value") for i in range(4)],
    # states for the 4 checkboxes
    [State(f"is_correct_{i}", "value") for i in range(4)],
)
def process_question_form(n_clicks, question_text, *states):
    if not n_clicks:
        raise PreventUpdate

    # unpack variable-length *states
    response_texts = states[:4]  # first 4 states
    correctness_flags = states[4:]  # last 4 states

    # Generate JSON for the question and responses
    question = {"question_text": question_text}
    responses = [
        {"response_text": response_texts[i], "is_correct": correctness_flags[i]}
        for i in range(4)
    ]

    # Validation
    errors = []

    if not question["question_text"] or not question["question_text"].strip():
        errors.append(html.P("Question text is required."))

    for idx, r in enumerate(responses, start=1):
        if not r["response_text"] or not r["response_text"].strip():
            errors.append(html.P(f"Option {idx} must have text."))
    correct_count = sum(1 for r in responses if r["is_correct"])

    if correct_count == 0:
        errors.append(html.P("Please select exactly one correct response (none selected)."))
    elif correct_count > 1:
        errors.append(html.P("Please select exactly one correct response (multiple selected)."))

    # Return the validation errors
    if errors:
        return errors

    # Use the API to save the question to the database
    payload = question
    try:
        response = requests.post(f"{API_BASE_URL}/question", json=payload)
        response.raise_for_status()

        # Get the id of the newly saved question from the response
        question_id = response.json()["id"]

        for idx, r in enumerate(responses, start=1):
            r["question_id"] = question_id
            resp = requests.post(f"{API_BASE_URL}/response", json=r)
            resp.raise_for_status()
        return "Question saved successfully."

    except Exception as exc:
        return html.P(f"Error saving question: {exc}")


if __name__ == '__main__':
    app.run(debug=True)
