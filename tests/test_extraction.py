from pathlib import Path

import pytest

from llmops_training.news_reader.extraction import (
    extract_businesses_involved,
    extract_general_info,
    format_prompt,
    get_businesses_involved_prompt_template,
    get_general_info_prompt_template,
)
from llmops_training.news_reader.logs import configure_structlog, configure_tracer

configure_structlog()
configure_tracer()

ARTICLES_DIR = Path(__file__).parent / "articles"
article_files = list(ARTICLES_DIR.glob("*.txt"))[:1]  # Only use the first article for now


@pytest.fixture(params=article_files)
def article(request):
    with open(request.param, "r", encoding="utf-8") as file:
        return file.read()


def test_format_prompt_article_only():
    article = "This is an article."
    prompt_template = "This is a prompt for the article:\n{article}"

    output = format_prompt(prompt_template, article)

    assert output == "This is a prompt for the article:\nThis is an article."


def test_format_prompt_article_and_business():
    article = "This is an article."
    business = "Company"
    prompt_template = "This is a prompt for the business '{business}':\n{article}"

    output = format_prompt(prompt_template, article, business)

    assert output == "This is a prompt for the business 'Company':\nThis is an article."


def test_summary_not_too_long(article: str):
    summary = extract_general_info(get_general_info_prompt_template(), article).summary
    summary_length = len(summary.split(". "))
    assert False # TODO: Fill me in! Assert that summary is <= 2 sentences


def test_extracted_businesses_are_in_article(article: str):
    businesses = extract_businesses_involved(
        get_businesses_involved_prompt_template(), article
    ).businesses
    for business in businesses:
        # TODO: Fill me in! Assert that the business is in the article
        assert False, f"Business '{business}' not found in the article"
