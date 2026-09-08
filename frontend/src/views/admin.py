import streamlit as st

from src.common.components import render_empty_state
from src.common.layout import apply_page_layout
from src.common.navbar import render_navbar
from src.views.admin_analytics import render_admin_analytics

ADMIN_MENU_ANALYTICS = "검색정보분석"
ADMIN_MENU_RESTAURANTS = "식당정보"
ADMIN_MENU_FEEDBACK = "사용자피드백"
ADMIN_MENU_KEY = "admin_menu"


def render_admin_sidebar():
    current_menu = st.session_state.get(ADMIN_MENU_KEY, ADMIN_MENU_ANALYTICS)

    st.caption("관리자 메뉴")

    if st.button(
        ADMIN_MENU_ANALYTICS,
        type="primary" if current_menu == ADMIN_MENU_ANALYTICS else "secondary",
        width="stretch",
        key="admin_menu_analytics_button",
    ):
        st.session_state[ADMIN_MENU_KEY] = ADMIN_MENU_ANALYTICS
        st.rerun()

    if st.button(
        ADMIN_MENU_RESTAURANTS,
        type="primary" if current_menu == ADMIN_MENU_RESTAURANTS else "secondary",
        width="stretch",
        key="admin_menu_restaurants_button",
    ):
        st.session_state[ADMIN_MENU_KEY] = ADMIN_MENU_RESTAURANTS
        st.rerun()

    if st.button(
        ADMIN_MENU_FEEDBACK,
        type="primary" if current_menu == ADMIN_MENU_FEEDBACK else "secondary",
        width="stretch",
        key="admin_menu_feedback_button",
    ):
        st.session_state[ADMIN_MENU_KEY] = ADMIN_MENU_FEEDBACK
        st.rerun()


def render_admin():
    apply_page_layout("dashboard")
    current_menu = st.session_state.setdefault(
        ADMIN_MENU_KEY,
        ADMIN_MENU_ANALYTICS,
    )
    render_navbar(current_menu, profile_type="0")

    sidebar_column, content_column = st.columns([0.22, 0.78], gap="medium")

    with sidebar_column:
        render_admin_sidebar()

    with content_column:
        if current_menu == ADMIN_MENU_ANALYTICS:
            render_admin_analytics()
        elif current_menu == ADMIN_MENU_RESTAURANTS:
            render_empty_state(
                "식당정보 화면은 이 담당 범위에 포함하지 않습니다.",
                next_action="검색정보분석 메뉴에서 로그 대시보드를 확인하세요.",
            )
        else:
            render_empty_state(
                "사용자피드백 화면은 이 담당 범위에 포함하지 않습니다.",
                next_action="검색정보분석 메뉴에서 로그 대시보드를 확인하세요.",
            )
