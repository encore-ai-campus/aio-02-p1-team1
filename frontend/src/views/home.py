from pathlib import Path

import streamlit as st


# =========================================================
# 경로 설정
# =========================================================

CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR.parent

CSS_PATH = SRC_DIR / "styles" / "home.css"


# =========================================================
# CSS 로드
# =========================================================

def load_home_css():
    """홈 화면 CSS를 불러온다."""

    if CSS_PATH.exists():
        css = CSS_PATH.read_text(encoding="utf-8")

        st.html(
            f'<style>{css}</style>'
        )


# =========================================================
# Navbar
# =========================================================

def render_navbar():

    st.html(
        f'<div class="playeat-navbar">'
        f'  <div class="playeat-logo-area">'
        f'    <div class="playeat-symbol">🍴</div>'
        f'    <div class="playeat-logo-text">'
        f'      <div class="playeat-logo">'
        f'        Play<span>EAT</span>'
        f'      </div>'
        f'      <div class="playeat-logo-sub">'
        f'        오늘의 한 끼, '
        f'        <strong>좋은 기억</strong>이 되도록'
        f'      </div>'
        f'    </div>'
        f'  </div>'
        f'  <div class="playeat-nav-menu">'
        f'    <div class="nav-item active">'
        f'      맛집 추천'
        f'    </div>'
        f'    <div class="nav-item">'
        f'      마이페이지'
        f'    </div>'
        f'    <div class="logout-button">'
        f'      👤 로그아웃'
        f'    </div>'
        f'  </div>'
        f'</div>'
    )

# =========================================================
# 채팅 화면
# =========================================================

def render_chat():

    messages = st.session_state.get("chat_messages", [])

    message_html = ""

    for message in messages:
        role = message.get("role", "assistant")
        content = message.get("content", "")

        if role == "user":
            message_html += (
                f'<div class="chat-row user-row">'
                f'  <div class="chat-message user-message">'
                f'    {content}'
                f'  </div>'
                f'</div>'
            )

        else:
            message_html += (
                f'<div class="chat-row assistant-row">'
                f'  <div class="chat-message assistant-message">'
                f'    {content}'
                f'  </div>'
                f'</div>'
            )

    st.html(
        f'''
        <div class="chat-box">
            <div class="chat-header">
                🍴 PlayEAT 추천 대화
            </div>

            <div class="chat-message-list">
                {message_html}
            </div>
        </div>
        '''
    )


# =========================================================
# 메인 제목
# =========================================================

def render_hero():

    st.html(
        f'<div class="home-hero">'
        f'  <h1>'
        f'    오늘은 어떤<br>'
        f'    <span>맛집</span>을 찾고<br>'
        f'    계신가요?'
        f'  </h1>'
        f'</div>'
    )


# =========================================================
# 검색창
# =========================================================

def render_search():

    search_col, button_col = st.columns(
        [8, 2],
        gap="small",
    )

    with search_col:
        keyword = st.text_input(
            "검색",
            placeholder="지역, 음식, 분위기 등을 입력해보세요",
            label_visibility="collapsed",
            key="home_search_keyword",
        )

    with button_col:
        search_clicked = st.button(
            "검색하기",
            key="home_search_button",
            type="primary",
            use_container_width=True,
        )

    return keyword, search_clicked


# =========================================================
# 카테고리 필터
# =========================================================

def render_filters():

    categories = [
        "🍲 한식",
        "🍕 양식",
        "🍱 일식",
        "🥟 중식",
        "☕ 카페",
        "👤 혼밥",
        "💰 가성비",
        "🕒 오래된 맛집",
    ]

    st.session_state.setdefault(
        "home_category",
        "🍲 한식",
    )

    cols = st.columns(
        [1, 1, 1, 1, 1, 1, 1.2, 1.5],
        gap="small",
    )

    for col, category in zip(cols, categories):

        with col:

            selected = (
                st.session_state.home_category
                == category
            )

            if st.button(
                category,
                key=f"home_filter_{category}",
                type="primary" if selected else "secondary",
                use_container_width=True,
            ):
                st.session_state.home_category = category
                st.rerun()


# =========================================================
# 추천 식당
# =========================================================

def render_restaurant():

    st.html(
        f'<div class="recommend-title">'
        f'  \'OO\'님을 위한 오늘의 추천 식당'
        f'</div>'
    )

    st.html(
        f'<div class="restaurant-card">'
        f'  <div class="restaurant-image">'
        f'    <div class="image-placeholder">'
        f'      식당 이미지'
        f'    </div>'
        f'  </div>'
        f'  <div class="restaurant-content">'
        f'    <div class="restaurant-name">'
        f'      서울식당'
        f'    </div>'
        f'    <div class="restaurant-address">'
        f'      서울 강남구 역삼동'
        f'    </div>'
        f'    <div class="restaurant-tags">'
        f'      <span>한식</span>'
        f'      <span>가성비</span>'
        f'    </div>'
        f'  </div>'
        f'</div>'
    )


# =========================================================
# 추천 이유
# =========================================================

def render_recommendation_reason():

    st.html(
        f'<div class="recommend-reason">'
        f'</div>'
    )


# =========================================================
# 만족도 평가
# =========================================================

def render_feedback():

    st.html(
        f'<div class="feedback-line"></div>'
        f'<div class="feedback-title">'
        f'  이 추천이 마음에 드셨나요?'
        f'</div>'
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "☺ 만족해요",
            key="home_feedback_good",
            use_container_width=True,
        ):
            st.session_state.feedback = "good"

    with col2:
        if st.button(
            "😐 보통이에요",
            key="home_feedback_normal",
            use_container_width=True,
        ):
            st.session_state.feedback = "normal"

    with col3:
        if st.button(
            "☹ 아쉬워요 (다른 곳 골라줘)",
            key="home_feedback_bad",
            use_container_width=True,
        ):
            st.session_state.feedback = "bad"


# =========================================================
# Home
# =========================================================

def render_home():

    load_home_css()

    render_navbar()

    with st.container(key="home_content"):

        render_hero()

        keyword, search_clicked = render_search()

        render_filters()

        # 검색 버튼 클릭
        if search_clicked:

            if keyword.strip():

                keyword = keyword.strip()

                st.session_state.search_keyword = keyword

                # 채팅 목록이 없으면 생성
                st.session_state.setdefault(
                    "chat_messages",
                    []
                )

                # 사용자 검색어 대화에 추가
                st.session_state.chat_messages.append(
                    {
                        "role": "user",
                        "content": keyword,
                    }
                )

                # 임시 AI 응답
                st.session_state.chat_messages.append(
                    {
                        "role": "assistant",
                        "content": "조건에 맞는 맛집을 찾아볼게요!",
                    }
                )

            else:
                st.warning(
                    "검색어를 입력해주세요."
                )

        # 검색한 기록이 있을 때만 채팅창 표시
        if st.session_state.get("chat_messages"):

            render_chat()

            render_restaurant()

            render_recommendation_reason()

            render_feedback()