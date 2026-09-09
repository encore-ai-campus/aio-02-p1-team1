import requests
import streamlit as st
from pathlib import Path


FASTAPI_BASE_URL = "http://127.0.0.1:8000"


def load_signup_css():
    css_path = (
        Path(__file__).parent.parent
        / "styles"
        / "signup.css"
    )

    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True,
        )


def render_signup():
    """회원가입 화면"""

    load_signup_css()

    # ==========================================
    # 1. 상단 로고
    # ==========================================

    st.markdown(
        """
        <div class="signup-navbar">
            <div class="brand-logo">
                <span class="brand-icon">🍴</span>
                <span>맛집친구</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ==========================================
    # 2. 회원가입 안내 문구
    # ==========================================

    st.markdown(
        """
        <div class="signup-label">
            맛있는
        </div>

        <div class="signup-title">
            새로운 맛집 생활을 시작해보세요
        </div>

        <div class="signup-description">
            AI가 추천하는 나만의 맛집을 만나보세요.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ==========================================
    # 3. 회원 정보 입력
    # ==========================================

    # 현재 UI 구조 유지를 위해 아이디 입력창은 남겨둡니다.
    # 단, MVP 인증은 이메일 + 비밀번호이므로
    # login_id는 회원가입 API로 전송하지 않습니다.
    login_id = st.text_input(
        "아이디",
        placeholder="아이디를 입력하세요",
        label_visibility="collapsed",
        key="signup_login_id",
    )

    email = st.text_input(
        "이메일",
        placeholder="이메일을 입력하세요",
        label_visibility="collapsed",
        key="signup_email",
    )

    password = st.text_input(
        "비밀번호",
        type="password",
        placeholder="비밀번호를 입력하세요",
        label_visibility="collapsed",
        key="signup_password",
    )

    password_confirm = st.text_input(
        "비밀번호 확인",
        type="password",
        placeholder="비밀번호를 다시 입력하세요",
        label_visibility="collapsed",
        key="signup_password_confirm",
    )

    username = st.text_input(
        "닉네임",
        placeholder="닉네임을 입력하세요",
        label_visibility="collapsed",
        key="signup_username",
    )

    # ==========================================
    # 4. 약관 동의
    # ==========================================

    terms_agreed = st.checkbox(
        "이용약관에 동의합니다.",
        key="signup_terms",
    )

    privacy_agreed = st.checkbox(
        "개인정보 수집 및 이용에 동의합니다.",
        key="signup_privacy",
    )

    # ==========================================
    # 5. 회원가입 버튼
    # ==========================================

    if st.button(
        "회원가입",
        use_container_width=True,
        key="signup_button",
    ):

        # --------------------------------------
        # 아이디 검증
        # 현재 UI를 유지하기 위한 검증이며
        # 실제 회원가입 API에는 보내지 않습니다.
        # --------------------------------------

        login_id = login_id.strip()

        if not login_id:
            st.error("아이디를 입력해주세요.")
            return

        if len(login_id) < 4 or len(login_id) > 20:
            st.error("아이디는 4~20자로 입력해주세요.")
            return

        # --------------------------------------
        # 이메일 검증
        # --------------------------------------

        email = email.strip()

        if not email:
            st.error("이메일을 입력해주세요.")
            return

        if "@" not in email:
            st.error("올바른 이메일 형식으로 입력해주세요.")
            return

        # --------------------------------------
        # 비밀번호 검증
        # --------------------------------------

        if not password:
            st.error("비밀번호를 입력해주세요.")
            return

        if len(password) < 8:
            st.error("비밀번호는 8자 이상 입력해주세요.")
            return

        if len(password) > 128:
            st.error("비밀번호는 128자 이하로 입력해주세요.")
            return

        if not password_confirm:
            st.error("비밀번호 확인을 입력해주세요.")
            return

        if password != password_confirm:
            st.error("비밀번호가 서로 다릅니다.")
            return

        # --------------------------------------
        # 닉네임 검증
        # 백엔드 SignUpRequest 기준: 1~45자
        # --------------------------------------

        username = username.strip()

        if not username:
            st.error("닉네임을 입력해주세요.")
            return

        if len(username) > 45:
            st.error("닉네임은 45자 이하로 입력해주세요.")
            return

        # --------------------------------------
        # 약관 동의 검증
        # --------------------------------------

        if not terms_agreed:
            st.error("이용약관에 동의해주세요.")
            return

        if not privacy_agreed:
            st.error(
                "개인정보 수집 및 이용에 동의해주세요."
            )
            return

        # ======================================
        # 6. FastAPI 회원가입 요청
        # ======================================

        try:
            response = requests.post(
                f"{FASTAPI_BASE_URL}/api/v1/auth/signups",
                json={
                    "email": email,
                    "password": password,
                    "nickname": username,
                    "terms_agreed": terms_agreed,
                    "privacy_agreed": privacy_agreed,
                },
                timeout=10,
            )

        except requests.exceptions.ConnectionError:
            st.error(
                "백엔드 서버에 연결할 수 없습니다. "
                "FastAPI 서버가 실행 중인지 확인해주세요."
            )
            return

        except requests.exceptions.Timeout:
            st.error(
                "회원가입 요청 시간이 초과되었습니다. "
                "잠시 후 다시 시도해주세요."
            )
            return

        except requests.exceptions.RequestException:
            st.error(
                "회원가입 요청 중 오류가 발생했습니다."
            )
            return

        # ======================================
        # 7. FastAPI 응답 처리
        # ======================================

        if response.status_code == 201:
            st.success(
                "회원가입이 완료되었습니다. 로그인해주세요."
            )
            return

        # 닉네임 또는 이메일 중복 등
        if response.status_code == 409:
            try:
                data = response.json()

                error = data.get("detail", {}).get("error", {})
                message = error.get(
                    "message",
                    "이미 사용 중인 이메일 또는 닉네임입니다.",
                )

                st.error(message)

            except (ValueError, AttributeError):
                st.error(
                    "이미 사용 중인 이메일 또는 닉네임입니다."
                )

            return

        # FastAPI / Pydantic 입력값 검증 오류
        if response.status_code == 422:
            st.error(
                "입력값을 다시 확인해주세요."
            )
            return

        # 그 외 서버 오류
        st.error(
            "회원가입 처리 중 오류가 발생했습니다. "
            "잠시 후 다시 시도해주세요."
        )

    # ==========================================
    # 8. 로그인 화면 이동
    # ==========================================

    st.markdown(
        """
        <div class="signup-footer">
            이미 계정이 있으신가요?
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "로그인하기",
        use_container_width=True,
        key="go_login_button",
    ):
        st.session_state.page = "login"
        st.rerun()