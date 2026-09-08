from textwrap import dedent

import streamlit as st


def render_navbar(current_menu, profile_type=None):
    caption = "관리자" if profile_type == "0" else "AI 맛집 추천 서비스"

    st.markdown(
        dedent(
            f"""
            <div class="playeat-navbar">
                <div>
                    <div class="playeat-logo">PlayEAT</div>
                    <div class="playeat-logo-caption">{caption}</div>
                </div>
                <div class="playeat-logo-caption">{current_menu}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )
