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

def test_run_evaluation(evaluation_data: pd.DataFrame):
    results = run_evaluation(evaluation_data)
    assert results["general_info_success_rate"] >= 0.8
    assert results["title_accuracy"] >= 0.5
    assert results["business_classification_accuracy"] >= 0.7
    assert results["summarization_rouge_1"] >= 0.15    # TODO: Fill me in! Choose pass rates for metrics and assert they are satisfied
# TODO: Fill me in! Add evaluation test that asserts pass rates are satisfied
