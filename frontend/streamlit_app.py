import streamlit as st

from src.views.admin import render_admin
from src.views.home import render_home
from src.views.login import render_login
from src.views.signup import render_signup
from src.views.mypage import render_mypage


# =========================
# Streamlit 기본 설정
# =========================

st.set_page_config(
    page_title="맛집친구",
    page_icon="🍴",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================
# 기본 페이지
# =========================

st.session_state.setdefault(
    "page",
    "home",
)


# =========================
# URL query parameter 처리
# 예: ?page=mypage
# =========================

query_page = st.query_params.get("page")


if query_page == "home":
    st.session_state["page"] = "home"

    st.query_params.clear()

    st.rerun()


elif query_page == "mypage":
    st.session_state["page"] = "mypage"

    st.query_params.clear()

    st.rerun()


elif query_page == "login":
    st.session_state["page"] = "login"

    st.query_params.clear()

    st.rerun()


elif query_page == "signup":
    st.session_state["page"] = "signup"

    st.query_params.clear()

    st.rerun()


elif query_page == "admin":
    st.session_state["page"] = "admin"

    st.query_params.clear()

    st.rerun()


elif query_page == "logout":
    st.session_state.clear()

    st.session_state["page"] = "login"

    st.query_params.clear()

    st.rerun()
# =========================
# 현재 페이지 출력
# =========================

page = st.session_state.page


if page == "home":
    render_home()

elif page == "login":
    render_login()

elif page == "signup":
    render_signup()

elif page == "mypage":
    render_mypage()

# elif page == "find_account":
#     render_find_account()

# elif page == "login_success":
#     render_login_success()

elif page == "admin":
    render_admin()
    