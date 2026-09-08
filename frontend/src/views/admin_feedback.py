from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from src.common.components import (
    render_empty_state,
    render_page_header,
    render_section_title,
)

FEEDBACK_LABELS = {
    "1": "아쉬움",
    "2": "보통이야",
    "3": "도움됨",
}
FEEDBACK_STATE_KEYS = {
    "period_start": "admin_feedback_period_start",
    "period_end": "admin_feedback_period_end",
    "feedback_value": "admin_feedback_value",
}


def get_default_period():
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(days=7)
    return period_start, period_end


def initialize_feedback_state():
    period_start, period_end = get_default_period()
    st.session_state.setdefault(FEEDBACK_STATE_KEYS["period_start"], period_start)
    st.session_state.setdefault(FEEDBACK_STATE_KEYS["period_end"], period_end)
    st.session_state.setdefault(FEEDBACK_STATE_KEYS["feedback_value"], "전체")


def parse_period_input(period_value):
    fallback_start, fallback_end = get_default_period()
    if isinstance(period_value, (list, tuple)) and len(period_value) == 2:
        start_date, end_date = period_value
    else:
        start_date = fallback_start.date()
        end_date = fallback_end.date()

    period_start = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if end_date == now.date():
        period_end = now
    else:
        period_end = datetime.combine(
            end_date,
            datetime.max.time().replace(microsecond=0),
            tzinfo=timezone.utc,
        )
    if period_start >= period_end:
        period_end = period_start + timedelta(days=1)
    return period_start, period_end


def render_feedback_filters():
    render_section_title("조회 조건")
    current_start = st.session_state[FEEDBACK_STATE_KEYS["period_start"]]
    current_end = st.session_state[FEEDBACK_STATE_KEYS["period_end"]]

    with st.form("admin_feedback_filter_form"):
        period_value = st.date_input(
            "조회 기간",
            value=(current_start.date(), current_end.date()),
            key="admin_feedback_period_input",
        )
        feedback_value = st.segmented_control(
            "사용자 반응",
            options=["전체", "아쉬움", "보통이야", "도움됨"],
            default=st.session_state.get(FEEDBACK_STATE_KEYS["feedback_value"]) or "전체",
            key="admin_feedback_value_input",
        )
        apply_clicked = st.form_submit_button("적용", type="primary")
        reset_clicked = st.form_submit_button("초기화")

    if apply_clicked:
        period_start, period_end = parse_period_input(period_value)
        st.session_state[FEEDBACK_STATE_KEYS["period_start"]] = period_start
        st.session_state[FEEDBACK_STATE_KEYS["period_end"]] = period_end
        st.session_state[FEEDBACK_STATE_KEYS["feedback_value"]] = (
            feedback_value or "전체"
        )
        st.rerun()

    if reset_clicked:
        period_start, period_end = get_default_period()
        st.session_state[FEEDBACK_STATE_KEYS["period_start"]] = period_start
        st.session_state[FEEDBACK_STATE_KEYS["period_end"]] = period_end
        st.session_state[FEEDBACK_STATE_KEYS["feedback_value"]] = "전체"
        st.session_state.pop("admin_feedback_period_input", None)
        st.session_state.pop("admin_feedback_value_input", None)
        st.rerun()


def render_feedback_kpis():
    render_section_title("추천 평가 지표")
    with st.container(horizontal=True):
        st.metric("전체 평가 수", "데이터 없음", border=True)
        st.metric("긍정 평가율", "데이터 없음", border=True)
        st.metric("중립 평가율", "데이터 없음", border=True)
        st.metric("부정 평가율", "데이터 없음", border=True)
        st.metric("평가 참여율", "데이터 없음", border=True)
    st.caption(
        "도움됨은 3, 보통이야는 2, 아쉬움은 1 입니다. 분모가 0이면 0%로 표시하지 않습니다."
    )


def render_feedback_charts():
    left_column, right_column = st.columns(2, gap="medium")
    with left_column:
        with st.container(border=True):
            st.subheader("평가 분포")
            render_empty_state(
                "전체 사용자 평가 집계 API가 설계서에 없습니다.",
                next_action="비율 차트를 0값으로 그리지 않습니다.",
            )
            st.caption("색상 기준: 도움됨 성공, 보통이야 주의, 아쉬움 위험")
    with right_column:
        with st.container(border=True):
            st.subheader("최근 평가")
            render_empty_state(
                "평가 목록을 조회할 관리자 API가 없습니다.",
                next_action="사용자 개인 통계 API로 관리자 화면을 채우지 않습니다.",
            )


def render_feedback_table():
    render_section_title("평가 목록")
    empty_df = pd.DataFrame(
        columns=["식당명", "평가", "추천 ID", "평가일"]
    )
    st.dataframe(empty_df, hide_index=True)
    render_empty_state("표시할 평가 행이 없습니다.")


def render_admin_feedback():
    initialize_feedback_state()
    render_page_header(
        "사용자피드백",
        "추천 평가를 아쉬움, 보통이야, 도움됨 기준으로 확인하고 분포와 목록을 봅니다.",
    )
    render_feedback_filters()
    period_start = st.session_state[FEEDBACK_STATE_KEYS["period_start"]]
    period_end = st.session_state[FEEDBACK_STATE_KEYS["period_end"]]
    st.caption(
        f"적용 기간: {period_start.strftime('%Y-%m-%d %H:%M')} ~ {period_end.strftime('%Y-%m-%d %H:%M')} UTC / 반응 필터: {st.session_state[FEEDBACK_STATE_KEYS['feedback_value']]}"
    )
    render_feedback_kpis()
    render_feedback_charts()
    render_feedback_table()
