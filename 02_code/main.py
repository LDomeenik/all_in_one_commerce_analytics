"""
main.py

Streamlit 앱 실행 진입점

기능:
    - Streamlit 페이지 기본 설정
    - 파일 업로드 화면 호출
    - 업로드 결과 상태 확인
    - Human Review 완료 여부 확인
"""


import streamlit as st

from python.app.ui.upload_page import render_upload_page


# main: Streamlit 앱 실행 흐름 제어
def main():
    """
    Streamlit 앱의 메인 실행 흐름 제어
    """

    # Streamlit 페이지 기본 설정
    st.set_page_config(
        page_title="All-in-One Commerce Analytics",
        layout="wide"
    )

    # 파일 업로드 화면 렌더링
    df, metadata, confirmed_mapping_result = render_upload_page()

    # Human Review 완료 후 다음 단계 안내 메시지
    if df is not None and metadata is not None and confirmed_mapping_result is not None:
        st.divider()
        st.subheader("다음 단계")
        st.write("확정된 컬럼 매핑 결과를 기반으로 전처리 단계로 이동할 수 있습니다.")


# 앱 실행
if __name__ == "__main__":
    main()