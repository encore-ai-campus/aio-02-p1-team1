from pathlib import Path

import streamlit as st

from src.common.api_client import get_json

# ----------------------------------------
# 페이지 기본 설정
# ----------------------------------------
st.set_page_config(
    page_title="맛집친구 - 마이페이지",
    page_icon="🍴",
    layout="wide",
)


# ----------------------------------------
# 마이페이지 디자인
# ----------------------------------------
def load_css(css_file: str) -> None:
    """외부 CSS 파일을 불러와 Streamlit 화면에 적용한다."""
    css = Path(css_file).read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)




def render_mypage():
    """마이페이지 화면을 보여준다."""

    # 마이페이지 CSS 적용하기
    load_css(Path(__file__).parent.parent / "styles" / "mypage.css")

    # ----------------------------------------
    # 로그인한 사용자 정보 가져오기
    # ----------------------------------------
    access_token = st.session_state.get("access_token")

    # 로그인 정보가 없으면 마이페이지를 보여주지 않는다.
    if not access_token:
        st.error("로그인이 필요합니다.")
        return

    # 백엔드에서 현재 로그인한 사용자의 정보를 가져온다.
    try:
        user = get_json(
            "/users/me",
            access_token=access_token,
        )
    except Exception as error:
        st.error(f"사용자 정보를 불러오지 못했습니다: {error}")
        return


    # ----------------------------------------
    # 최근 좋아요 식당 가져오기
    # ----------------------------------------
    try:
        likes_data = get_json(
            "/users/me/likes",
            access_token=access_token,
        )

        recent_restaurants = likes_data.get("restaurants", [])

    except Exception as error:
        st.error(f"좋아요 식당 정보를 불러오지 못했습니다: {error}")
        recent_restaurants = []

    # ----------------------------------------
    # 자주 사용하는 태그 가져오기
    # ----------------------------------------
    try:
        tags_data = get_json(
            "/users/me/tags",
            access_token=access_token,
        )

        # 화면에 표시할 수 있도록 태그 앞에 # 붙이기
        favorite_tags = [
            f"#{tag}"
            for tag in tags_data.get("tags", [])
        ]

    except Exception as error:
        st.error(f"태그 정보를 불러오지 못했습니다: {error}")
        favorite_tags = []

    # ----------------------------------------
    # 선호 음식 카테고리 비율 가져오기
    # ----------------------------------------
    try:
        categories_data = get_json(
            "/users/me/categories",
            access_token=access_token,
        )

        favorite_categories = categories_data.get("categories", {})

    except Exception as error:
        st.error(f"카테고리 정보를 불러오지 못했습니다: {error}")
        favorite_categories = {}

    # ----------------------------------------
    # 상단 인사
    # ----------------------------------------
    title_col, button_col = st.columns([4, 1])

    with title_col:
        st.markdown(
            f'<p class="mypage-title">'
            f'안녕하세요, {user["nickname"]} 님! 👋'
            f'</p>'
            f'<p class="mypage-subtitle">'
            f'오늘도 맛있는 하루 보내세요.'
            f'</p>',
            unsafe_allow_html=True,
        )

    with button_col:
        if st.button(
            "프로필 수정 ❯",
            use_container_width=True,
        ):
            st.session_state["mypage_view"] = "profile"
            st.rerun()

    # ----------------------------------------
    # 자주 사용한 태그
    # ----------------------------------------
    if favorite_tags:
        tags_html = "".join(
            f'<span class="tag">{tag}</span>'
            for tag in favorite_tags
        )

        tag_card = (
            '<div class="tag-card">'
            '<span class="tag-icon">◇</span>'
            '<strong>자주 사용한 태그는</strong>'
            f'{tags_html}'
            '<span> 이에요!</span>'
            '</div>'
        )

    else:
        tag_card = (
            '<div class="tag-card">'
            '<span class="tag-icon">◇</span>'
            '<strong>최근에는 사용한 태그가 없어요.</strong>'
            '</div>'
        )

    st.markdown(
        tag_card,
        unsafe_allow_html=True,
    )

    # ----------------------------------------
    # 카드 2개
    # ----------------------------------------
    left, right = st.columns(
        2,
        gap="medium",
    )

    # ----------------------------------------
    # 왼쪽 카드
    # 최근에 좋아요를 남겨주신 곳
    # ----------------------------------------
    with left:
        restaurant_html = ""

        for restaurant in recent_restaurants:
            restaurant_html += (
                '<div class="restaurant-item">'
                '<div class="restaurant-top">'
                f'<span class="restaurant-name">'
                f'{restaurant["name"]}'
                f'</span>'
                '</div>'
                f'<div class="restaurant-location">'
                f'📍 {restaurant.get("address") or "주소 정보 없음"}'
                f'</div>'
                '</div>'
            )

        left_card = (
            '<div class="mypage-card">'
            '<div class="card-title">'
            '<span class="card-icon">♡</span>'
            '최근에 좋아요를 남겨주신 곳'
            '</div>'
            f'{restaurant_html}'
            '</div>'
        )

        st.markdown(
            left_card,
            unsafe_allow_html=True,
        )

    # ----------------------------------------
    # 오른쪽 카드
    # 자주 드시는 메뉴
    # ----------------------------------------
    with right:
        categories = list(favorite_categories.items())

        legend_html = ""

        for index, (category, value) in enumerate(
            categories,
            start=1,
        ):
            legend_html += (
                '<div class="legend-row">'
                f'<span class="legend-dot dot-{index}"></span>'
                f'<span class="legend-name">{category}</span>'
                f'<span class="legend-value">{value}%</span>'
                '</div>'
            )

        right_card = (
            '<div class="mypage-card">'
            '<div class="card-title">'
            '<span class="card-icon">🍴</span>'
            '자주 드시는 메뉴'
            '</div>'
            '<div class="menu-content">'
            '<div class="donut">'
            '<div class="donut-center">'
            '<div class="donut-label">총</div>'
            '<div class="donut-total">100%</div>'
            '</div>'
            '</div>'
            '<div class="menu-legend">'
            f'{legend_html}'
            '</div>'
            '</div>'
            '</div>'
        )

        st.markdown(
            right_card,
            unsafe_allow_html=True,
        )


# ----------------------------------------
# 마이페이지 단독 실행
# 팀 프로젝트에 합칠 때는 제거한다.
# ----------------------------------------
if __name__ == "__main__":
    render_mypage()