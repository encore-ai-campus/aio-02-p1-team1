from pathlib import Path

import streamlit as st
# from app.db import supabase

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


    load_css(Path(__file__).parent.parent / "styles" / "mypage.css")
    # ----------------------------------------
    # 임시 사용자 데이터
    # 나중에 DB/API 데이터로 변경한다.
    # ----------------------------------------
    user = {
        "nickname": "맛집러버",
        "user_id": "EXAM_ID",
        "email": "example@email.com",
    }

    # 최근 좋아요를 누른 식당 3개
    recent_restaurants = [
        {
            "name": "강남 손칼국수",
            "location": "서울 강남구 대치동",
            "date": "2026.09.03",
        },
        {
            "name": "싸다 김밥",
            "location": "서울 서초구 서초동",
            "date": "2026.09.02",
        },
        {
            "name": "역삼파스타",
            "location": "서울 강남구 역삼동",
            "date": "2026.09.01",
        },
    ]

    # 최근 한 달 동안 자주 사용한 태그
    favorite_tags = [
        "#한식",
        "#가성비",
        "#혼밥",
    ]

    # 자주 선택한 음식 종류
    favorite_categories = {
        "한식": 40,
        "일식": 25,
        "양식": 15,
        "중식": 10,
        "카페/디저트": 7,
        "기타": 3,
    }


# # ----------------------------------------
# # 실제 마이페이지 데이터 가져오기
# # ----------------------------------------

# # 현재 로그인한 사용자의 PK
# # profiles.id는 Supabase auth.users.id와 1:1로 연결된다.
# profile_id = st.session_state["user_id"]


# # 사용자 프로필 가져오기
# # 새 DB 구조에서는 profiles에 이메일 컬럼이 없고,
# # 이메일은 Supabase Auth(auth.users)에서 관리한다.
# profile_result = (
#     supabase
#     .table("profiles")
#     .select("id, profile_login_id, profile_nickname")
#     .eq("id", profile_id)
#     .eq("profile_status", "1")
#     .single()
#     .execute()
# )
#
# profile = profile_result.data
#
# # 로그인한 사용자의 이메일은 Supabase Auth에서 가져온다.
# auth_user = supabase.auth.get_user()
#
# user = {
#     "nickname": profile["profile_nickname"],
#     "user_id": profile["profile_login_id"],
#     "email": auth_user.user.email,
# }


# # 최근 좋아요를 누른 식당 3개 가져오기
# # feedback_value = '3'이 좋아요이며, 최신순으로 조회한다.
# feedback_result = (
#     supabase
#     .table("feedback")
#     .select("restaurant_id, created_at")
#     .eq("profile_id", profile_id)
#     .eq("feedback_value", "3")
#     .order("created_at", desc=True)
#     .limit(3)
#     .execute()
# )
#
# recent_restaurants = []
#
# for feedback in feedback_result.data:
#
#     # feedback.restaurant_id와 연결된 식당 정보를 가져온다.
#     restaurant_result = (
#         supabase
#         .table("restaurants")
#         .select("id, name, address")
#         .eq("id", feedback["restaurant_id"])
#         .single()
#         .execute()
#     )
#
#     restaurant = restaurant_result.data
#
#     recent_restaurants.append(
#         {
#             "restaurant_id": restaurant["id"],
#             "name": restaurant["name"],
#             "location": restaurant["address"] or "주소 정보 없음",
#             "date": feedback["created_at"][:10].replace("-", "."),
#         }
#     )


# # 최근 한 달 동안 자주 사용한 태그
# # 현재 DB에는 '사용자가 어떤 태그를 검색/선택했는지'를 저장하는
# # 사용자별 태그 사용 이력 테이블이 없으므로 아직 계산할 수 없다.
# favorite_tags = []


# # 자주 드시는 메뉴(선호 음식 카테고리 비율)
# # 좋아요(feedback_value = '3')를 남긴 식당의 category_id를 기준으로
# # 카테고리별 비율을 계산할 수 있다.
# # 실제 서비스에서는 이 계산을 백엔드 API에서 처리하는 것을 권장한다.
# liked_result = (
#     supabase
#     .table("feedback")
#     .select("restaurant_id")
#     .eq("profile_id", profile_id)
#     .eq("feedback_value", "3")
#     .execute()
# )
#
# category_counts = {}
# total_count = 0
#
# for feedback in liked_result.data:
#     restaurant_result = (
#         supabase
#         .table("restaurants")
#         .select("category_id")
#         .eq("id", feedback["restaurant_id"])
#         .single()
#         .execute()
#     )
#
#     category_id = restaurant_result.data.get("category_id")
#
#     if category_id is None:
#         continue
#
#     category_result = (
#         supabase
#         .table("restaurant_categories")
#         .select("name")
#         .eq("id", category_id)
#         .single()
#         .execute()
#     )
#
#     category_name = category_result.data["name"]
#     category_counts[category_name] = category_counts.get(category_name, 0) + 1
#     total_count += 1
#
# favorite_categories = {}
#
# if total_count > 0:
#     favorite_categories = {
#         category: round(count / total_count * 100)
#         for category, count in category_counts.items()
#     }



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
                f'<span class="restaurant-date">'
                f'{restaurant["date"]}'
                f'</span>'
                '</div>'
                f'<div class="restaurant-location">'
                f'📍 {restaurant["location"]}'
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
render_mypage()