from dash.testing.application_runners import import_app
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def test_h2_text_equals(dash_duo):
    """
    GIVEN the app is running (dash_duo runs the app and provides a webdriver)
    WHEN the home page is available
    THEN the first h2 element should have the text 'Charts'
    """
    # Start the server
    app = import_app(app_file="paralympics.app")
    dash_duo.start_server(app)

    # Uses a Dash API function to wait for a h2 element on the page
    dash_duo.wait_for_element("h2", timeout=4)

    # Find all H2 elements on the page
    h2_els = dash_duo.find_elements("h2")

    # Assert that the first h2 heading text is "Charts"
    assert h2_els[0].text == "Charts"


def test_line_chart_displays(dash_duo):
    """
    GIVEN a server
    WHEN the selector with id=`select-chart` is found and the option with value=`line` selected
    AND the selector with id=`line-select` is visible and the option with value=`sports` selected
    THEN a plotly chart with the css class `.js-plotly-plot` should be present
    """
    app = import_app(app_file="paralympics.app")
    dash_duo.start_server(app)

    # Choose the 'line' chart type
    dash_duo.wait_for_element("#select-chart", timeout=4)
    dash_duo.find_element("#select-chart option[value='line']").click()

    # Wait for the line-specific selector and choose 'sports'
    dash_duo.wait_for_element("#line-select", timeout=4)
    dash_duo.find_element("#line-select option[value='sports']").click()

    # Assert a Plotly chart is present
    dash_duo.wait_for_element(".js-plotly-plot", timeout=6)
    plot = dash_duo.find_element(".js-plotly-plot")
    assert plot is not None



def test_answer_question_correct(dash_duo):
    """
    GIVEN a server URL
    WHEN the 'home' page is requested
    AND the answer to a question is selected and submitted and is correct
    THEN a new question should be displayed
    """
    app = import_app(app_file="paralympics.app")
    dash_duo.start_server(app)

    # Get the question element text
    question_el_1 = dash_duo.find_element("#question-label")

    # Select the radio input with value="1" and click it
    dash_duo.wait_for_element("input[type='radio'][value='1']", timeout=4)
    dash_duo.find_element("input[type='radio'][value='1']").click()

    # Get the question element text
    question_el2 = dash_duo.find_element("#question-label")

    # assert that the question text has changed
    assert question_el_1.text != question_el2.text


def test_new_question_submitted(dash_duo):
    """
    GIVEN a server URL (dash_duo hosts the app)
    WHEN the Teacher admin tab is selected (<a role="tab">Teacher admin</a>)
    AND textarea with id="question_text" has the text for a new question entered
    AND response_text_0..3 are completed
    AND is_correct_0 is checked
    AND #new-question-submit-button is clicked
    THEN #form-message contains "Question saved successfully."
    """

    app = import_app(app_file="paralympics.app")
    dash_duo.start_server(app)

    driver = dash_duo.driver
    wait = WebDriverWait(driver, 10)

    def fill_with_actions(css_selector: str, text: str):
        """Click into an input/textarea and type text using ActionChains."""
        el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
        chain = ActionChains(driver)
        (
            chain.move_to_element(el)
                 .click()
                 # Clear existing content (Ctrl/Cmd + A, Delete)
                 .key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL)
                 .send_keys(Keys.DELETE)
                 .send_keys(text)
                 .perform()
        )

    # 1) Click the "Teacher admin" tab (role="tab", case-insensitive match)
    tab = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "//a[@role='tab' and contains(translate(normalize-space(.),"
        " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
        " 'teacher admin')]"
    )))
    ActionChains(driver).move_to_element(tab).click().perform()

    # 2) Fill inputs
    fill_with_actions("#question_text", "New question")
    fill_with_actions("#response_text_0", "A is correct")
    fill_with_actions("#response_text_1", "B is incorrect")
    fill_with_actions("#response_text_2", "C is incorrect")
    fill_with_actions("#response_text_3", "D is incorrect")

    # Check the correct checkbox if not already selected
    is_correct_0 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#is_correct_0")))
    if not is_correct_0.is_selected():
        ActionChains(driver).move_to_element(is_correct_0).click().perform()

    # Submit
    submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#new-question-submit-button")))
    ActionChains(driver).move_to_element(submit).click().perform()

    # Assert
    msg = dash_duo.find_element("#form-message").text
    assert "Question saved successfully." in msg