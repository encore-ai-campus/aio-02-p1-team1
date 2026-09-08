from pathlib import Path

import streamlit as st


# ----------------------------------------
# 프로필 수정 전용 CSS 불러오기
# ----------------------------------------
def load_profile_edit_css():
    """프로필 수정 화면 전용 CSS를 적용한다."""

    css_path = (
        Path(__file__).parent.parent
        / "styles"
        / "profile_edit.css"
    )

    css = css_path.read_text(encoding="utf-8")

    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True,
    )


# ----------------------------------------
# 간단한 HTML 출력 함수
# ----------------------------------------
def render_html(html):
    """HTML 문자열을 Streamlit 화면에 출력한다."""

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


# ----------------------------------------
# 프로필 수정 화면
# ----------------------------------------
def render_profile_edit(user):
    """로그인한 사용자의 프로필 수정 화면을 보여준다."""

    load_profile_edit_css()

    # ========================================
    # 페이지 제목
    # ========================================
    render_html(
        '<div class="profile-edit-header">'
        '<h1 class="profile-edit-title">프로필 수정</h1>'
        '<p class="profile-edit-subtitle">'
        '내 정보를 수정하고, 더 나은 맛집 경험을 만들어보세요.'
        '</p>'
        '</div>'
    )

    # ========================================
    # 기본 정보 카드
    # ========================================
    with st.container(
        key="profile_edit_card",
        border=False,
    ):

        render_html(
            '<h2 class="profile-edit-section-title">'
            '기본 정보'
            '</h2>'
        )

        # ====================================
        # 닉네임
        # 왼쪽: 라벨
        # 오른쪽: 입력창
        # ====================================
        nickname_label_col, nickname_input_col = st.columns(
            [1.2, 6],
            vertical_alignment="center",
        )

        with nickname_label_col:
            render_html(
                '<div class="profile-edit-field-label">'
                '닉네임 '
                '<span class="profile-edit-required">*</span>'
                '</div>'
            )

        with nickname_input_col:

            with st.container(
                key="profile_nickname_field",
                border=False,
            ):

                nickname = st.text_input(
                    "닉네임",
                    value=user.get("nickname", ""),
                    max_chars=20,
                    key="profile_edit_nickname",
                    label_visibility="collapsed",
                )

                render_html(
                    f'<div class="profile-edit-count">'
                    f'{len(nickname)}/20'
                    f'</div>'
                )

        # ====================================
        # 이메일
        # 이메일은 수정할 수 없다.
        # ====================================
        email_label_col, email_input_col = st.columns(
            [1.2, 6],
            vertical_alignment="top",
        )

        with email_label_col:
            render_html(
                '<div class="profile-edit-field-label">'
                '이메일'
                '</div>'
            )

        with email_input_col:
            st.text_input(
                "이메일",
                value=user.get("email", ""),
                disabled=True,
                key="profile_edit_email",
                label_visibility="collapsed",
            )

            render_html(
                '<p class="profile-edit-help">'
                '이메일은 변경할 수 없습니다.'
                '</p>'
            )

        # ====================================
        # 비밀번호
        # ====================================
        password_label_col, password_content_col = st.columns(
            [1.2, 6],
            vertical_alignment="center",
        )

        with password_label_col:
            render_html(
                '<div class="profile-edit-field-label">'
                '비밀번호'
                '</div>'
            )

        with password_content_col:

            with st.container(
                key="profile_password_box",
                border=False,
            ):

                password_info_col, password_button_col = st.columns(
                    [4, 1.6],
                    vertical_alignment="center",
                )

                with password_info_col:
                    render_html(
                        '<div class="profile-password-info">'
                        '<div class="profile-password-icon">🔒</div>'
                        '<div class="profile-password-copy">'
                        '<p class="profile-password-title">'
                        '비밀번호를 안전하게 관리하고 계신가요?'
                        '</p>'
                        '<p class="profile-password-description">'
                        '주기적으로 비밀번호를 변경하여 '
                        '계정을 안전하게 보호하세요.'
                        '</p>'
                        '</div>'
                        '</div>'
                    )

                with password_button_col:
                    if st.button(
                        "비밀번호 변경",
                        key="go_password_change",
                        use_container_width=True,
                    ):
                        # 다음 단계에서
                        # 실제 비밀번호 변경 화면으로 연결한다.
                        st.info(
                            "비밀번호 변경 기능은 다음 단계에서 구현합니다."
                        )

        # ====================================
        # 구분선
        # ====================================
        render_html(
            '<div class="profile-edit-divider"></div>'
        )

        # ====================================
        # 하단 버튼
        # ====================================
        empty_col, cancel_col, save_col = st.columns(
            [3.8, 1.2, 1.5],
            vertical_alignment="center",
        )

        # 취소
        with cancel_col:
            if st.button(
                "취소",
                key="profile_edit_cancel",
                use_container_width=True,
            ):
                st.session_state["mypage_view"] = "main"
                st.rerun()

        # 저장
        with save_col:
            if st.button(
                "저장하기",
                key="profile_edit_save",
                type="primary",
                use_container_width=True,
            ):

                cleaned_nickname = nickname.strip()

                # 닉네임 검증
                if not cleaned_nickname:
                    st.error(
                        "닉네임을 입력해주세요."
                    )

                elif len(cleaned_nickname) > 20:
                    st.error(
                        "닉네임은 20자 이하로 입력해주세요."
                    )

                else:
                    # 다음 단계에서 FastAPI PATCH API 연결
                    st.success(
                        "현재는 화면만 구현된 상태입니다."
                    )