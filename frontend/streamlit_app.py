import streamlit as st

st.set_page_config(
    page_title="테스트",
    layout="wide",
)

st.title("Streamlit 실행 테스트")

st.success("✅ Streamlit 정상 구동 중!")
st.write("streamlit_app.py가 정상적으로 실행되었습니다.")