from pathlib import Path

import streamlit as st


from src.common.api_client import (
    get_json,
    post_json,
    stream_post,
)


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

        # 맛집 추천
        f'    <a href="?page=home" class="nav-item active">'
        f'      맛집 추천'
        f'    </a>'

        # 마이페이지
        f'    <a href="?page=mypage" class="nav-item">'
        f'      마이페이지'
        f'    </a>'

        # 로그아웃
        f'    <a href="?page=logout" class="logout-button">'
        f'      👤 로그아웃'
        f'    </a>'

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
    """
    각 그룹별 하나씩 선택 가능

    restaurant_categories
        한식 / 중식 / 일식 / 양식 / 기타

    menu_types
        매운거 / 든든한거 / 국물여부

    price_levels
        인당가격_하 / 인당가격_중 / 인당가격_상
    """

    st.session_state.setdefault(
        "home_restaurant_category",
        None,
    )

    st.session_state.setdefault(
        "home_menu_type",
        None,
    )

    st.session_state.setdefault(
        "home_price_level",
        None,
    )


    # =====================================================
    # 1. 음식 종류
    # =====================================================

    st.markdown("#### 음식 종류")

    restaurant_categories = [
        ("🍲 한식", "한식"),
        ("🥟 중식", "중식"),
        ("🍱 일식", "일식"),
        ("🍕 양식", "양식"),
        ("🍴 기타", "기타"),
    ]

    cols = st.columns(
        5,
        gap="small",
    )

    for col, (label, value) in zip(
        cols,
        restaurant_categories,
    ):
        with col:
            selected = (
                st.session_state[
                    "home_restaurant_category"
                ]
                == value
            )

            if st.button(
                label,
                key=f"filter_restaurant_{value}",
                type=(
                    "primary"
                    if selected
                    else "secondary"
                ),
                use_container_width=True,
            ):
                if selected:
                    st.session_state[
                        "home_restaurant_category"
                    ] = None
                else:
                    st.session_state[
                        "home_restaurant_category"
                    ] = value

                st.rerun()


    # =====================================================
    # 2. 음식 특징 + 가격대
    # 한 줄에 출력
    # =====================================================

    st.markdown("#### 음식 특징 / 가격대")

    menu_types = [
        ("🔥 매운거", "매운거"),
        ("🥩 든든한거", "든든한거"),
        ("🍲 국물", "국물여부"),
    ]

    price_levels = [
        ("💰 가성비", "인당가격_하"),
        ("💵 중간쯤", "인당가격_중"),
        ("💎 비싼거", "인당가격_상"),
    ]

    # 총 6개 버튼 한 줄
    cols = st.columns(
        6,
        gap="small",
    )


    # -----------------------------
    # 음식 특징 3개
    # -----------------------------

    for col, (label, value) in zip(
        cols[:3],
        menu_types,
    ):
        with col:
            selected = (
                st.session_state[
                    "home_menu_type"
                ]
                == value
            )

            if st.button(
                label,
                key=f"filter_menu_{value}",
                type=(
                    "primary"
                    if selected
                    else "secondary"
                ),
                use_container_width=True,
            ):
                if selected:
                    st.session_state[
                        "home_menu_type"
                    ] = None
                else:
                    st.session_state[
                        "home_menu_type"
                    ] = value

                st.rerun()


    # -----------------------------
    # 가격대 3개
    # -----------------------------

    for col, (label, value) in zip(
        cols[3:],
        price_levels,
    ):
        with col:
            selected = (
                st.session_state[
                    "home_price_level"
                ]
                == value
            )

            if st.button(
                label,
                key=f"filter_price_{value}",
                type=(
                    "primary"
                    if selected
                    else "secondary"
                ),
                use_container_width=True,
            ):
                if selected:
                    st.session_state[
                        "home_price_level"
                    ] = None
                else:
                    st.session_state[
                        "home_price_level"
                    ] = value

                st.rerun()


    return {
        "restaurant_category": (
            st.session_state[
                "home_restaurant_category"
            ]
        ),
        "menu_type": (
            st.session_state[
                "home_menu_type"
            ]
        ),
        "price_level": (
            st.session_state[
                "home_price_level"
            ]
        ),
    }


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
# 대화방이 없으면 생성하는 함수
# =========================================================

def ensure_conversation():

    access_token = st.session_state.get(
        "access_token"
    )

    # 로그인 토큰 확인
    if not access_token:
        st.warning(
            "access_token이 없습니다. 로그인 상태를 확인해주세요."
        )
        return False

    # 이미 대화방이 있으면 사용
    conversation_id = st.session_state.get(
        "conversation_id"
    )

    if conversation_id:
        return True

    # 대화방 생성
    result = post_json(
        "/conversations",
        json_body={
            "title": "맛집 추천 대화",
        },
        access_token=access_token,
    )

    # 생성 실패
    if not result["ok"]:
        st.error(
            f"대화방 생성 실패: {result['error']['message']}"
        )
        return False

    # 생성된 conversation_id 저장
    conversation_id = result["data"]["id"]

    st.session_state[
        "conversation_id"
    ] = conversation_id

    # 새 대화방이므로 기존 로드 상태 초기화
    st.session_state[
        "chat_loaded"
    ] = False

    return True

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


    # -----------------------------------------
    # 1. 대화방 확인 / 생성
    # -----------------------------------------
    conversation_ready = ensure_conversation()

    # -----------------------------------------
    # 2. 기존 메시지 조회
    # -----------------------------------------
    if conversation_ready:
        load_chat_messages()

    with st.container(
        key="home_content",
    ):

        render_hero()

        keyword, search_clicked = render_search()

        # 필터 선택값
        filters = render_filters()

        # 기존 채팅
        if st.session_state.get(
            "chat_messages"
        ):
            render_chat()

        # 검색 버튼
        if search_clicked:

            keyword = keyword.strip()

            if keyword:

                st.session_state[
                    "search_keyword"
                ] = keyword

                handle_chat(
                    keyword,
                    filters,
                )

            else:
                st.warning(
                    "검색어를 입력해주세요."
                )

        # 추천 결과
        if st.session_state.get(
            "chat_messages"
        ):

            render_restaurant()

            render_recommendation_reason()

            render_feedback()


# 기존 대화 불러오기
def load_chat_messages():
    conversation_id = st.session_state.get("conversation_id")
    access_token = st.session_state.get("access_token")

    if not conversation_id or not access_token:
        return

    if st.session_state.get("chat_loaded"):
        return

    result = get_json(
        f"/conversations/{conversation_id}/messages",
        access_token=access_token,
    )

    if not result["ok"]:
        st.error(result["error"]["message"])
        return

    messages = result["data"] or []

    st.session_state.chat_messages = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in messages
        if message["role"] in ("user", "assistant")
    ]

    st.session_state.chat_loaded = True

#채팅 전송
def handle_chat(
    keyword: str,
    filters: dict,
):
    conversation_id = st.session_state.get(
        "conversation_id"
    )

    access_token = st.session_state.get(
        "access_token"
    )

    if not conversation_id:
        st.error("대화방 정보가 없습니다.")
        return

    if not access_token:
        st.error("로그인이 필요합니다.")
        return

    st.session_state.setdefault(
        "chat_messages",
        [],
    )

    st.session_state.chat_messages.append(
        {
            "role": "user",
            "content": keyword,
        }
    )

    assistant_text = ""

    for event in stream_post(
        f"/conversations/{conversation_id}/chat",
        json_body={
            "content": keyword,
            "restaurant_category": filters.get(
                "restaurant_category"
            ),
            "menu_type": filters.get(
                "menu_type"
            ),
            "price_level": filters.get(
                "price_level"
            ),
        },
        access_token=access_token,
        timeout=60,
    ):
        if "error" in event:
            st.error(event["error"])
            return

        if "text" in event:
            assistant_text += event["text"]

        if event.get("done"):
            st.session_state[
                "last_message_id"
            ] = event.get(
                "message_id"
            )

    if assistant_text:
        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": assistant_text,
            }
        )

    st.rerun()