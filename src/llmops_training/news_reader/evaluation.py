from typing import Dict, List, Optional

import dotenv
import nltk
import pandas as pd
import structlog
from nltk.tokenize import word_tokenize
from rouge import Rouge

from llmops_training.news_reader.data import get_evaluation_data
from llmops_training.news_reader.extraction import (
    GeneralInfo,
    extract_business_category_from_articles,
    extract_general_info_from_articles,
    get_business_category_prompt_template,
    get_general_info_prompt_template,
)
from llmops_training.news_reader.logs import configure_structlog, configure_tracer

logger = structlog.get_logger()

nltk.download("punkt")
dotenv.load_dotenv()


# TODO: Fill me in! Add the `evaluate_business_classification` function


def evaluate_extract_general_info_success_rate(
    general_info_list: List[Optional[GeneralInfo]],
) -> float:
    """Return success rate of extraction of general info."""

    n_articles = len(general_info_list)
    n_success = len([info for info in general_info_list if info is not None])

    success_rate = n_success / n_articles
    return success_rate


def evaluate_title(general_info_list: List[Optional[GeneralInfo]], data: pd.DataFrame) -> float:
    """Return accuracy of extracting the title.

    Data should contain:
    - a column "title" with the title of the article.

    The provided list of general info should be in the same order as the data.
    """

    n_success = 0
    n_articles = 0
    for i, row in data.iterrows():
        if general_info_list[i] is None:
            continue

        # We ignore the " - BBC News" suffix for comparison
        title = row["title"].lower().replace(" - bbc news", "")
        extracted_title = general_info_list[i].title.lower().replace(" - bbc news", "")

        n_articles += 1
        if extracted_title == title:
            n_success += 1

    accuracy = n_success / n_articles
    return accuracy


def evaluate_summarization(general_info_list, data) -> Dict[str, float]:
    """Return average ROUGE score of summarization of articles.

    Data should contain:
    - a column "description" with a summary of the article.

    The provided list of general info should be in the same order as the data.
    """

    rouge = Rouge()
    scores: Dict[str, List[float]] = {"rouge-1": [], "rouge-2": [], "rouge-l": []}
    for i, row in data.iterrows():
        if general_info_list[i] is None:
            continue

        given_summary = row["description"]
        generated_summary = general_info_list[i].summary

        generated_summary_tokens = " ".join(word_tokenize(generated_summary.lower()))
        given_summary_tokens = " ".join(word_tokenize(given_summary.lower()))

        score = rouge.get_scores(generated_summary_tokens, given_summary_tokens)[0]

        scores["rouge-1"].append(score["rouge-1"]["f"])
        scores["rouge-2"].append(score["rouge-2"]["f"])
        scores["rouge-l"].append(score["rouge-l"]["f"])

    avg_scores = {
        "rouge-1": sum(scores["rouge-1"]) / len(scores["rouge-1"]),
        "rouge-2": sum(scores["rouge-2"]) / len(scores["rouge-2"]),
        "rouge-l": sum(scores["rouge-l"]) / len(scores["rouge-l"]),
    }

    return avg_scores


def run_evaluation(data: pd.DataFrame) -> Dict[str, float]:
    """Run evaluation functions on given data set and log and return metrics"""
    assert "article" in data.columns
    assert "is_business" in data.columns
    assert "description" in data.columns
    assert "title" in data.columns

    general_info_prompt_template = get_general_info_prompt_template()
    general_info_list = extract_general_info_from_articles(
        general_info_prompt_template, data["article"].to_list()
    )

    business_category_prompt_template = get_business_category_prompt_template()
    business_category_list = extract_business_category_from_articles(
        business_category_prompt_template, data["article"].to_list()
    )

    success_rate = evaluate_extract_general_info_success_rate(general_info_list)
    title_accuracy = evaluate_title(general_info_list, data)
    summarization_scores = evaluate_summarization(general_info_list, data)

    # business_classification_accuracy = evaluate_business_classification(
    #     business_category_list, data
    # )  # TODO: Uncomment me!

    metrics = {
        "general_info_success_rate": success_rate,
        "title_accuracy": title_accuracy,
        # "business_classification_accuracy": business_classification_accuracy,  # TODO: Uncomment me!
        "summarization_rouge_1": summarization_scores["rouge-1"],
        "summarization_rouge_2": summarization_scores["rouge-2"],
        "summarization_rouge_l": summarization_scores["rouge-l"],
    }

    print("evaluation", metrics)  # TODO(11-bonus): Convert this to a structured log (use **metrics)

    return metrics


if __name__ == "__main__":
    configure_structlog()
    configure_tracer()

    data = get_evaluation_data()
    run_evaluation(data)
