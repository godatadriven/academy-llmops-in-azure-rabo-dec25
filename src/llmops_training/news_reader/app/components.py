"""Defines the components of the Streamlit app defined in the `app` module."""

import os
from typing import Optional

import dotenv
import streamlit as st
import logging
import structlog
from streamlit.delta_generator import DeltaGenerator

from llmops_training.news_reader.logs import configure_tracer
from llmops_training.news_reader.app import utils
from llmops_training.news_reader.extraction import (
    mock_extract_info_from_articles,
    extract_info_from_articles
)

dotenv.load_dotenv()

configure_tracer()
logging.basicConfig(level=logging.INFO)
structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())

logger = structlog.get_logger()


def article_upload_form(position: DeltaGenerator) -> None:
    """Allows user to upload articles, and directly extract information from them."""
    with position.form("article_form", clear_on_submit=True):
        st.write("📥 **Extract from Articles**")

        uploaded_articles = st.file_uploader(
            "Upload your articles", type=["txt", "md"], accept_multiple_files=True
        )
        pasted_articles = st.text_area("Type or paste your article")

        articles_submitted = st.form_submit_button("Extract info")
        if articles_submitted:
            st.session_state["articles"] = []
            if uploaded_articles:
                for uploaded_file in uploaded_articles:
                    st.session_state["articles"].append(uploaded_file.getvalue().decode("utf-8"))
            if pasted_articles:
                st.session_state["articles"].append(pasted_articles)

            articles = st.session_state["articles"]

            # Create a structured log entry for the number of articles added
            # ... # TODO(11-monitor-functional-metrics): Fill me in! Add log statement
            logging.info("started on article file")

            # Exract structured information using the `mock_extract_info_from_articles` function
            results, _ = extract_info_from_articles(articles)
                #[None] * len(articles), ...)  # TODO(03-running-the-app/04-modularizing-the-solution): Replace me!

            # TODO(13-feedback-with-trace): Make sure trace IDs from `extract_info_from_articles`
            # are returned and stored in the session state `st.session_state["trace_ids"]`

            st.session_state["results"] = results

            utils.success_message(st, "Articles processed!", seconds=1)
            st.rerun()


def article_stats(position: DeltaGenerator) -> None:
    """Shows simple statistics about the uploaded articles."""
    with position.container(border=True):
        st.write("📊 **Article Stats**")
        st.write(f"Number of articles: {len(st.session_state['articles'])}")


def article_selector(position: DeltaGenerator) -> Optional[int]:
    """Allows user to select an article from the uploaded ones.

    If only one article is available, it is automatically selected.
    """
    with position.container(border=True):
        st.write("🎯 **Select Article**")
        if len(st.session_state["articles"]) == 0:
            st.write("_No articles added yet._")
            doc_index = None
        elif len(st.session_state["articles"]) == 1:
            st.write("_Only one article available._")
            doc_index = 0
        else:
            doc_index = st.slider("Article", 0, len(st.session_state["articles"]) - 1, 0)
    return doc_index


def display_article(position: DeltaGenerator, doc_index: Optional[int]):
    """Displays the selected article for the user to read."""
    with position.container(border=True):
        st.write("📃 **Selected Article**")

        if doc_index is None:
            st.write("_No article selected yet._")
            return

        st.markdown(st.session_state["articles"][doc_index], unsafe_allow_html=True)


def display_results(position: DeltaGenerator, doc_index: Optional[int]):
    """Displays the extracted structured information for the selected article."""
    with position.container(border=True):
        st.write("🗂️ **Structured Output**")

        if doc_index is None:
            st.write("_No results available yet._")
            return

        if st.session_state["results"][doc_index] is None:
            st.write("_An error occurred while processing this article._")
            return

        for key, value in st.session_state["results"][doc_index].model_dump().items():
            if key == "business_info" and len(value) > 0:
                st.markdown(f"`{key}`:")
                for i, value_dict in enumerate(value):
                    st.write(value_dict)  # TODO(13-collect-feedback): Replace me!
                    # ... # Add feedback collection with `utils.write_and_collect_feedback`
                    # use button_key=f"{key}_{i}" and result_key=key
                    # you can also add json_payload={"business": value_dict["business"]}
                    # Hint: add your "user_name" to the json_payload for later filtering

            elif key != "business_info":
                if isinstance(value, bool):
                    value = ":green[TRUE]" if value else ":red[FALSE]"
                value = f"`{key}`: {value}"

                st.write(value)  # TODO(13-collect-feedback): Replace me!
                # ... # Add feedback collection with `utils.write_and_collect_feedback`
                # use button_key=key and result_key=key
                # Hint: add your "user_name" to the json_payload for later filtering

        saved = st.button("Save result")
        if saved:
            utils.success_message(st, "Result saved successfully!", seconds=1)
