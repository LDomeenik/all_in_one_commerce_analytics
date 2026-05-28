"""
main.py

Streamlit 앱 진입점 모듈

기능:
    - Streamlit 페이지 기본 설정
    - session_state 초기화
    - 사이드바 네비게이션 구성
    - 각 페이지 렌더링 호출
"""


import streamlit as st

from app.streamlit.session import init_session, get_state, RAW_DF, STAGING_DF
from app.streamlit.views.upload_page import render_upload_page
from app.streamlit.views.mapping_page import render_mapping_page


# 페이지 기본 설정
st.set_page_config(
    page_title="All-in-One Commerce Analytics",
    page_icon="📊",
    layout="wide"
)


# main: Streamlit 앱 실행 흐름 제어
def main():
    """
    Streamlit 앱의 메인 실행 흐름을 제어합니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    # session_state 초기화
    init_session()

    # 사이드바 네비게이션
    st.sidebar.title("📊 Commerce Analytics")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "페이지 선택",
        options=["데이터 업로드", "컬럼 매핑"],
        index=0
    )

    st.sidebar.divider()

    # 진행 상태 표기
    st.sidebar.write("#### 진행 상태")

    if get_state(RAW_DF) is not None:
        st.sidebar.write("✅ 데이터 업로드 완료")
    else:
        st.sidebar.write("⬜ 데이터 업로드 대기 중")

    if get_state(STAGING_DF) is not None:
        st.sidebar.write("✅ 컬럼 매핑 완료")
    else:
        st.sidebar.write("⬜ 컬럼 매핑 대기 중")
    
    # 페이지 렌더링
    if page == "데이터 업로드":
        render_upload_page()
    elif page == "컬럼 매핑":
        render_mapping_page()


if __name__ == "__main__":
    main()