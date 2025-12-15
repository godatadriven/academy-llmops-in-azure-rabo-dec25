import time
from typing import Any, Dict, Literal, Optional, Tuple

import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit_extras.grid import grid

from llmops_training.news_reader.logs import log_with_trace


def success_message(position: DeltaGenerator, message: str, seconds: int = 1) -> None:
    """Temporarily shows a success message."""
    pop_up = position.success(message)
    time.sleep(seconds)
    pop_up.empty()


def write_with_feedback_buttons(value: Any, button_key: str) -> Tuple[bool, bool]:
    """Writes a value to the screen with upvote and downvote buttons next to it."""
    result_grid = grid([0.8, 0.1, 0.1])
    result_grid.write(value)
    upvote = result_grid.button("👍", key=f"upvote_{button_key}")
    downvote = result_grid.button("👎", key=f"downvote_{button_key}")
    return upvote, downvote


def save_feedback(
    feedback: Literal["upvote", "downvote"],
    doc_index: int,
    result_key: str,
    json_payload: Optional[Dict] = None,
) -> None:
    """Saves feedback to the logs."""
    json_payload = json_payload or {}
    log_with_trace(
        "feedback",
        json_payload={"feedback": feedback, "result_key": result_key, **json_payload},
        trace_id=st.session_state["trace_ids"][doc_index],
    )


def write_and_collect_feedback(
    value: Any,
    doc_index: int,
    button_key: str,
    result_key: str,
    json_payload: Optional[Dict] = None,
) -> None:
    """Writes a value with feedback buttons and saves the feedback if a button is pressed."""
    upvote, downvote = write_with_feedback_buttons(value, button_key=button_key)

    if upvote or downvote:
        feedback: Literal["upvote", "downvote"] = "upvote" if upvote else "downvote"
        save_feedback(feedback, doc_index, result_key, json_payload)
        success_message(st, "Feedback saved", seconds=1)
