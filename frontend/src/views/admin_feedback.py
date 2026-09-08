import pandas as pd
import streamlit as st

from src.common.components import (
    render_empty_state,
    render_section_title,
    render_sentiment_cards,
)

FEEDBACK_TABLE_COLUMNS = [
    "번호",
    "작성일시",
    "식당명",
    "음식별",
    "가격대",
    "메뉴 특성",
    "사용자 반응",
]


def render_recommendation_satisfaction():
    render_section_title(
        "추천 결과 만족도",
        "만족은 도움됨, 보통은 보통이야, 불만족은 아쉬움과 같습니다.",
    )
    render_sentiment_cards(
        [
            {"label": "만족", "value": None, "tone": "success"},
            {"label": "보통", "value": None, "tone": "warning"},
            {"label": "불만족", "value": None, "tone": "danger"},
        ]
    )
    render_empty_state(
        "관리자 추천 평가 집계 API가 없어 비율을 표시하지 않습니다.",
        next_action="시안 수치를 사실처럼 넣지 않습니다.",
    )


def render_feedback_table():
    rows = []
    table_df = pd.DataFrame(columns=FEEDBACK_TABLE_COLUMNS)

    render_section_title("사용자 피드백 내역", f"표시 {len(rows)}건")
    if table_df.empty:
        st.dataframe(table_df, hide_index=True)
        render_empty_state(
            "평가 목록을 조회할 관리자 API가 없습니다.",
            next_action="사용자 개인 통계 API로 관리자 화면을 채우지 않습니다.",
        )
        return

    st.dataframe(table_df, hide_index=True)


def render_admin_feedback():
    render_recommendation_satisfaction()
    render_feedback_table()
