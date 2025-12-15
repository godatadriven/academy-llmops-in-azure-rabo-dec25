import pandas as pd
import pytest

from llmops_training.news_reader.data import get_evaluation_data
from llmops_training.news_reader.evaluation import run_evaluation
from llmops_training.news_reader.logs import configure_structlog, configure_tracer

configure_structlog()
configure_tracer()


@pytest.fixture
def evaluation_data() -> pd.DataFrame:
    return get_evaluation_data()


# TODO: Fill me in! Add evaluation test that asserts pass rates are satisfied
