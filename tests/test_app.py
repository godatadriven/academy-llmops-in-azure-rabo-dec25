from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def streamlit_app() -> AppTest:
    path_to_app = Path(__file__).parent / "../src/llmops_training/news_reader/app/app.py"
    return AppTest.from_file(path_to_app.as_posix()).run(timeout=30)


def test_app(streamlit_app: AppTest):
    msg = "Streamlit app did not run without errors."
    assert streamlit_app.session_state["$$STREAMLIT_INTERNAL_KEY_SCRIPT_RUN_WITHOUT_ERRORS"], msg


def test_upload_articles(streamlit_app: AppTest):
    # We can add all kinds of tests for app interactions, see:
    # https://docs.streamlit.io/develop/api-reference/app-testing
    assert True
