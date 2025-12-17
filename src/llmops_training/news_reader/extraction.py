from typing import List, Literal, Optional, Tuple

import dotenv
import structlog
from opentelemetry import trace
from pydantic import BaseModel, Field

from llmops_training.news_reader.generation import generate_object
from llmops_training.news_reader.logs import log_extraction_step, log_with_trace

tracer = trace.get_tracer(__name__)
#logger = structlog.get_logger()

dotenv.load_dotenv()


class GeneralInfo(BaseModel):
    title: str = Field(..., description="The title of the article")
    summary: str = Field(..., description="A single sentence summary of the article")


class BusinessCategory(BaseModel):
    is_about_business: bool = Field(..., description="Whether the article is about business")


class BusinessesInvolved(BaseModel):
    businesses: List[str] = Field(
        ..., description="Which main businesses or companies are involved in the article"
    )


class BusinessSpecificInfo(BaseModel):
    business: str = Field(..., description="The business or company involved")
    stock_price_change: Literal["increase", "decrease", "none"] = Field(
        ...,
        description="""
        Possible stock price change as result of the article.
        - "increase" if article speaks positively about the business
        - "decrease" if article speaks negatively about the business
        - "none" if article speaks neutrally about the business
        """,
    )
    reason: str = Field(
        ..., description="A single sentence reason for the possible stock price change"
    )
    relevant_substring: str = Field(
        ..., description="A relevant substring from the article supporting the reason (10-20 words)"
    )


class ArticleInfo(BaseModel):
    title: str = Field(..., description="The title of the article")
    summary: str = Field(..., description="A single sentence summary of the article")
    is_about_business: bool = Field(..., description="Whether the article is about business")
    business_info: List[BusinessSpecificInfo]


def get_general_info_prompt_template() -> str:
    return "Extract structured information from the following article:\n{article}"


def get_business_category_prompt_template() -> str:
    return "Extract structured information from the following article:\n{article}"


def get_businesses_involved_prompt_template() -> str:
    return "Extract structured information from the following article:\n{article}"


def get_business_specific_prompt_template() -> str:
    return (
        "Extract structured information for the business '{business}' "
        + "from the following article:\n{article}"
    )


def format_prompt(prompt_template: str, article: str, business: Optional[str] = None) -> str:
    """Format the prompt with the article and business if provided"""
    assert "{article}" in prompt_template, "Prompt must contain placeholder '{article}'"
    if business is not None:
        assert "{business}" in prompt_template, "Prompt must contain placeholder '{business}'"
        return prompt_template.format(article=article, business=business)
    return prompt_template.format(article=article)

@tracer.start_as_current_span("extract_general_info", attributes={"service.name": "jasper"})
def extract_general_info(prompt_template: str, article: str, **kwargs) -> GeneralInfo:
    """Extract general information from an article, such as title and summary"""
    prompt = format_prompt(prompt_template, article)
    output = generate_object(prompt, GeneralInfo, **kwargs)

    log_extraction_step(
        trace.get_current_span().name, article, prompt_template, output.model_dump()
    )
    return output


@tracer.start_as_current_span("extract_business_category", attributes={"service.name": "jasper"})
def extract_business_category(prompt_template: str, article: str, **kwargs) -> BusinessCategory:
    """Extract whether an article is about business"""
    prompt = format_prompt(prompt_template, article)
    output = generate_object(prompt, BusinessCategory, **kwargs)
    log_extraction_step(
        trace.get_current_span().name, article, prompt_template, output.model_dump()
    )
    return output


@tracer.start_as_current_span("extract_businesses_involved", attributes={"service.name": "jasper"})
def extract_businesses_involved(prompt_template: str, article: str, **kwargs) -> BusinessesInvolved:
    """Extract which businesses are involved in an article"""
    prompt = format_prompt(prompt_template, article)
    output = generate_object(prompt, BusinessesInvolved, **kwargs)
    log_extraction_step(
        trace.get_current_span().name, article, prompt_template, output.model_dump()
    )
    return output


@tracer.start_as_current_span("extract_business_specific_info", attributes={"service.name": "jasper"})
def extract_business_specific_info(
    prompt_template: str, article: str, business: str, **kwargs
) -> BusinessSpecificInfo:
    """Extract specific information about a business from an article, such as stock price change"""
    prompt = format_prompt(prompt_template, article, business=business)
    output = generate_object(prompt, BusinessSpecificInfo, **kwargs)
    log_extraction_step(
        trace.get_current_span().name, article, prompt_template, output.model_dump(), business
    )
    return output


def is_business_we_care_about(business: str) -> bool:
    return True  # Some logic here


@tracer.start_as_current_span("extract_business_info", attributes={"service.name": "jasper"})
def extract_business_info(
    businesses_involved_prompt_template: str,
    business_specific_prompt_template: str,
    article: str,
    **kwargs,
) -> List[BusinessSpecificInfo]:
    """Extract information about businesses involved in an article"""
    businesses = extract_businesses_involved(
        businesses_involved_prompt_template, article
    ).businesses
    business_info = []
    for business in businesses:
        if is_business_we_care_about(business):
            business_info.append(
                extract_business_specific_info(
                    business_specific_prompt_template, article, business, **kwargs
                )
            )
    return business_info


@tracer.start_as_current_span("extract_article_info", attributes={"service.name": "jasper"})
def extract_article_info(article: str, **kwargs) -> Tuple[ArticleInfo, int]:
    """Return structured information from an article, and trace ID.

    This is a toy example of a modular approach to LLM apps. Some steps in our use case
    may become over-modularized, but it can be useful for more complex applications.
    """

    log_with_trace(trace.get_current_span().name, json_payload={"article": article})

    general_info = extract_general_info(
        get_general_info_prompt_template(),
        article=article,
        **kwargs,
    )
    business_category = extract_business_category(
        get_business_category_prompt_template(),
        article=article,
        **kwargs,
    )

    business_info = []
    if business_category.is_about_business:
        business_info = extract_business_info(
            get_businesses_involved_prompt_template(),
            get_business_specific_prompt_template(),
            article=article,
            **kwargs,
        )

    article_info = ArticleInfo(
        title=general_info.title,
        summary=general_info.summary,
        is_about_business=business_category.is_about_business,
        business_info=business_info,
    )

    # TODO(13-feedback-with-trace): replace mock trace_id with
    
    trace_id = trace.get_current_span().get_span_context().trace_id
    return article_info, trace_id


def extract_info_from_articles(
    articles: List[str],
) -> Tuple[List[Optional[ArticleInfo]], List[int]]:
    """Return structured information from a list of articles, and trace IDs."""
    article_infos = []
    trace_ids = []
    for article in articles:
        try:
            article_info, trace_id = extract_article_info(article)
        except Exception as e:
            article_info = None
            trace_id = trace.get_current_span().get_span_context().trace_id
            # Can we log the exception here to Azure? Yes!
        article_infos.append(article_info)
        trace_ids.append(trace_id)

    return article_infos, trace_ids


def extract_general_info_from_articles(
    prompt_template: str, articles: List[str]
) -> List[Optional[GeneralInfo]]:
    """Extract general information from a list of articles

    If an error occurs during extraction, the output will be None.
    """
    general_info_list = []
    for i, article in enumerate(articles):
        try:
            general_info = extract_general_info(prompt_template, article)
        except Exception as e:
            general_info = None
            print(f"Exception in article {i}: {e}")
        general_info_list.append(general_info)
    return general_info_list


def extract_business_category_from_articles(
    prompt_template: str, articles: List[str]
) -> List[Optional[BusinessCategory]]:
    """Extract business category from a list of articles

    If an error occurs during extraction, the output will be None.
    """
    business_category_list = []
    for i, article in enumerate(articles):
        try:
            business_category = extract_business_category(prompt_template, article)
        except Exception as e:
            business_category = None
            print(f"Exception in article {i}: {e}")
        business_category_list.append(business_category)
    return business_category_list


def mock_extract_article_info(article: str) -> Tuple[ArticleInfo, int]:
    """Returns mock extraction of structured info from an article, and trace ID."""
    trace_id = 1234567890
    article_info = ArticleInfo(
        title="Mock title",
        summary="Mock summary",
        is_about_business=True,
        business_info=[
            BusinessSpecificInfo(
                business="Mock business",
                stock_price_change="increase",
                reason="Mock reason",
                relevant_substring="Mock substring",
            )
        ],
    )
    return article_info, trace_id


def mock_extract_info_from_articles(articles: List[str]) -> Tuple[List[ArticleInfo], List[int]]:
    """Returns mock extraction of structured info from a list of articles, and trace IDs."""
    article_infos = []
    trace_ids = []
    for article in articles:
        article_info, trace_id = mock_extract_article_info(article)
        article_infos.append(article_info)
        trace_ids.append(trace_id)

    return article_infos, trace_ids


