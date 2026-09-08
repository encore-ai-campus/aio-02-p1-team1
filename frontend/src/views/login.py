from pathlib import Path

import requests
import streamlit as st


def load_login_css():
    css_path = (
        Path(__file__).resolve().parents[1]
        / "styles"
        / "login.css"
    )

    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True,
        )




def render_login():
    load_login_css()
    # 이미 로그인했다면 완료 화면으로 이동
    if st.session_state.get("user"):
        st.session_state.page = "login_success"
        st.rerun()


    login_col, image_col = st.columns(
        [0.94, 1.06],
        gap="large",
    )

    with login_col:
        st.markdown(
            """
<div class="login-main-title">
오늘, <span class="orange-text">어디서</span> 먹을까요?
</div>
<div class="login-description">
AI가 내 취향과 상황에 맞는 맛집을 찾아드려요.
</div>
""",
            unsafe_allow_html=True,
        )

        email = st.text_input(
            "이메일",
            placeholder="이메일을 입력하세요",
            key="login_email",
        )

        password = st.text_input(
            "비밀번호",
            placeholder="비밀번호를 입력하세요",
            type="password",
            key="login_password",
        )

        remember_col, find_col = st.columns([0.95, 1.05])

        with remember_col:
            # 기존 UI 유지. 브라우저 재접속 후 유지 기능은 미구현
            st.checkbox(
                "로그인 상태 유지",
                key="login_remember",
            )

        with find_col:
            if st.button(
                "ID / 비밀번호 찾기",
                key="find_account_button",
                use_container_width=True,
            ):
                st.session_state.page = "find_account"
                st.rerun()

        if st.button(
            "로그인",
            type="primary",
            use_container_width=True,
            key="login_button",
        ):
            if not email.strip() or not password:
                st.warning("이메일과 비밀번호를 입력해주세요.")

            else:
                try:
                    response = requests.post(
                        "http://127.0.0.1:8000/api/v1/auth/login",
                        json={
                            "email": email.strip(),
                            "password": password,
                        },
                        timeout=10,
                    )

                except requests.RequestException:
                    st.error(
                        "백엔드 서버에 연결할 수 없습니다. "
                        "서버 실행 상태를 확인해주세요."
                    )

                else:
                    if response.status_code == 200:
                        data = response.json()

                        st.session_state.user = data["user"]
                        st.session_state.access_token = data["access_token"]

                        if data["user"]["profile_type"] == "0":
                            st.session_state.page = "admin"
                        else:
                            st.session_state.page = "login_success"

                        st.rerun()

                    elif response.status_code == 401:
                        st.error(
                            "이메일 또는 비밀번호가 올바르지 않습니다."
                        )

                    elif response.status_code == 403:
                        st.error(
                            "사용할 수 없는 계정입니다."
                        )

                    elif response.status_code == 404:
                        st.error(
                            "사용자 프로필 정보를 찾을 수 없습니다."
                        )

                    else:
                        st.error(
                            "로그인 처리 중 오류가 발생했습니다."
                        )

        st.markdown(
            '<div class="signup-guide">계정이 없으신가요?</div>',
            unsafe_allow_html=True,
        )

        if st.button(
            "회원가입하기",
            key="go_signup",
            use_container_width=True,
        ):
            st.session_state.page = "signup"
            st.rerun()

    with image_col:
        image_path = (
            Path(__file__).resolve().parents[2]
            / "assets"
            / "login_food.jpg"
        )

        if image_path.is_file():
            st.image(image_path, width="stretch")
        else:
            st.warning(
                "assets/login_food.jpg 파일을 찾을 수 없습니다."
            )