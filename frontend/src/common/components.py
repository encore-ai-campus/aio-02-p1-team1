from textwrap import dedent

import streamlit as st

CHART_PRIMARY = "#FF7A00"
CHART_SECONDARY = "#FFB368"
CHART_SUCCESS = "#2E7D32"
CHART_WARNING = "#E08A00"
CHART_DANGER = "#C62828"
CHART_TEXT = "#333333"
CHART_MUTED = "#666666"
CHART_BORDER = "#DDDDDD"


def render_page_header(title, caption):
    st.markdown(
        dedent(
            f"""
            <h1 class="playeat-page-title">{title}</h1>
            <p class="playeat-page-caption">{caption}</p>
            """
        ),
        unsafe_allow_html=True,
    )


def render_section_title(title):
    st.markdown(
        f'<h2 class="playeat-section-title">{title}</h2>',
        unsafe_allow_html=True,
    )


def render_status_card(kind, title, message, meta_text=None):
    meta_html = ""
    if meta_text:
        meta_html = f'<p class="playeat-status-meta">{meta_text}</p>'

    st.markdown(
        dedent(
            f"""
            <div class="playeat-status-card">
                <p class="playeat-status-label {kind}">{title}</p>
                <p class="playeat-status-body">{message}</p>
                {meta_html}
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


def render_loading_state(message="조회 중입니다."):
    render_status_card("loading", "Loading", message)


def render_empty_state(message, next_action=None):
    action_text = next_action or "기간이나 필터를 바꾼 뒤 다시 적용해 주세요."
    render_status_card("empty", "Empty", f"{message} {action_text}")


def render_error_state(message, request_id=None, next_action=None):
    action_text = next_action or "잠시 후 다시 조회해 주세요."
    meta_text = None
    if request_id:
        meta_text = f"request_id: {request_id}"
    render_status_card(
        "error",
        "Error",
        f"{message} {action_text}",
        meta_text=meta_text,
    )
