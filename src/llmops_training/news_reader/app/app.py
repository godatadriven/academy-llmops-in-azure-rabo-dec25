"""Main application entry point for the News Reader app.
Makes use of app components defined in the `components` module.
"""

import streamlit as st

from llmops_training.news_reader.app import components
from llmops_training.news_reader.logs import configure_structlog, configure_tracer


@st.cache_resource()
def configure_logging_and_tracing():
    configure_structlog()
    configure_tracer()


def init_session_state():
    if "articles" not in st.session_state:
        st.session_state["articles"] = []
    if "results" not in st.session_state:
        st.session_state["results"] = []
    if "trace_ids" not in st.session_state:
        st.session_state["trace_ids"] = []


st.set_page_config(
    page_title="News Reader",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

configure_logging_and_tracing()
init_session_state()

st.sidebar.header("🗞️ Articles")
components.article_stats(st.sidebar)
doc_index = components.article_selector(st.sidebar)
components.article_upload_form(st.sidebar)

st.subheader("📑 News Reader")
cols = st.columns(2)
components.display_article(cols[0], doc_index)
components.display_results(cols[1], doc_index)
