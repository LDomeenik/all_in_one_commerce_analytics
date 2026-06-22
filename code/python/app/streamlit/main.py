"""
main.py

Streamlit 앱 진입점 모듈

기능:
    - Streamlit 페이지 기본 설정
    - session_state 초기화
    - 사이드바 렌더링 호출
    - 선택된 페이지 렌더링 호출
"""


import streamlit as st

from app.streamlit.session import init_session
from app.streamlit.sidebar import render_sidebar

from app.streamlit.views.upload_page import render_upload_page
from app.streamlit.views.mapping_page import render_mapping_page
from app.streamlit.views.preprocessing_page import render_preprocessing_page
from app.streamlit.views.diagnosis_page import render_diagnosis_page
from app.streamlit.views.eda_page import render_eda_page
from app.streamlit.views.kpi_page import render_kpi_page
from app.streamlit.views.cohort_page import render_cohort_page
from app.streamlit.views.rfm_page import render_rfm_page
from app.streamlit.views.product_page import render_product_page
from app.streamlit.views.delivery_page import render_delivery_page


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

    # 사이드바 렌더링
    page = render_sidebar()

    # 페이지 렌더링
    if page == "데이터 업로드":
        render_upload_page()
    elif page == "컬럼 매핑":
        render_mapping_page()
    elif page == "전처리":
        render_preprocessing_page()
    elif page == "진단":
        render_diagnosis_page()
    elif page == "EDA":
        render_eda_page()
    elif page == "KPI":
        render_kpi_page()
    elif page == "Cohort":
        render_cohort_page()
    elif page == "RFM":
        render_rfm_page()
    elif page == "상품":
        render_product_page()
    elif page == "배송/운영":
        render_delivery_page()


if __name__ == "__main__":
    main()