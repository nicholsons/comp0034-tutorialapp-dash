import re

from playwright.sync_api import Page, expect


def test_page_has_body(page: Page, app_server):
    """
    GIVEN a server URL (dash_app_server fixture yields the URL)
    WHEN the 'home' page is requested
    THEN the page body should be visible
    """
    page.goto(app_server)
    expect(page.locator("body")).to_be_visible()


def test_line_chart_displays(page: Page, app_server):
    """
    GIVEN a server URL
    WHEN the 'home' page is requested
    AND the line chart is chosen
    AND the sports data is chosen
    THEN a plotly line chart should be visible
    """
    # GIVEN a server URL
    page.goto(app_server)
    # WHEN the 'home' page is requested AND the line chart is chosen
    page.locator("#select-chart").select_option("line")
    # AND the sports data is chosen
    page.locator("#line-select").select_option("sports")
    # THEN a plotly line chart should be visible
    expect(page.locator(".js-plotly-plot")).to_be_visible()


def test_answer_question_correct(page: Page, app_server):
    """
    GIVEN a server URL
    WHEN the 'home' page is requested
    AND the answer to a question is selected and submitted and is correct
    THEN a new question should be displayed
    """
    page.goto(app_server)
    page.get_by_role("radio", name="Lillehammer").check()
    page.get_by_role("button", name="Submit answer").click()
    expect(page.get_by_text("How many participants were")).to_contain_text("?")


def test_new_question_submitted(page: Page, app_server):
    """
    GIVEN a server URL
    WHEN the home page is requested and the Teacher admin tab is selected (<a role="tab">Teacher admin</a>)
    AND textarea with id="question_text" has the text for a new question entered
    AND response_text_0, response_text_1, response_text_2 and response_text_3 are completed
    AND one of is_correct_0, is_correct_1, is_correct_2 and is_correct_3 is True
    AND "new-question-submit-button" is clicked
    THEN if the requests to the REST API with a new question and 4 responses are successful, a
    response should be displayed to the 'id="new-question-submit-button"
    with text "Question saved successfully.".
    """
    page.goto(app_server)
    page.get_by_role("tab").get_by_text(re.compile("teacher admin", re.IGNORECASE)).click()
    page.locator("#question_text").fill("New question")
    page.locator("#response_text_0").fill("A is correct")
    page.locator("#response_text_1").fill("B is incorrect")
    page.locator("#response_text_2").fill("C is incorrect")
    page.locator("#response_text_3").fill("D is incorrect")
    page.locator("#is_correct_0").check()
    page.locator("#new-question-submit-button").click()
    expect(page.locator("#form-message")).to_contain_text("Question saved successfully.")
