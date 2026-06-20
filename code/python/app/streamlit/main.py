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

from app.streamlit.session import (
    init_session, 
    get_state, 
    RAW_DF, 
    STAGING_DF, 
    PREPROCESSED_DF, 
    DIAGNOSIS_RESULT,
    EDA_RESULT,
    KPI_RESULT,
    COHORT_RESULT,
    RFM_RESULT,
    PRODUCT_RESULT
)

from app.streamlit.views.upload_page import render_upload_page
from app.streamlit.views.mapping_page import render_mapping_page
from app.streamlit.views.preprocessing_page import render_preprocessing_page
from app.streamlit.views.diagnosis_page import render_diagnosis_page
from app.streamlit.views.eda_page import render_eda_page
from app.streamlit.views.kpi_page import render_kpi_page
from app.streamlit.views.cohort_page import render_cohort_page
from app.streamlit.views.rfm_page import render_rfm_page
from app.streamlit.views.product_page import render_product_page


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
        options=["데이터 업로드", "컬럼 매핑", "전처리", "진단", "EDA", "KPI", "Cohort", "RFM", "상품"],
        index=0
    )

    st.sidebar.divider()

    # 진행 상태 표시
    st.sidebar.write("#### 진행 상태")

    if get_state(RAW_DF) is not None:
        st.sidebar.write("✅ 데이터 업로드 완료")
    else:
        st.sidebar.write("⬜ 데이터 업로드 대기 중")

    if get_state(STAGING_DF) is not None:
        st.sidebar.write("✅ 컬럼 매핑 완료")
    else:
        st.sidebar.write("⬜ 컬럼 매핑 대기 중")

    if get_state(PREPROCESSED_DF) is not None:
        st.sidebar.write("✅ 전처리 완료")
    else:
        st.sidebar.write("⬜ 전처리 대기 중")
    
    if get_state(DIAGNOSIS_RESULT) is not None:
        st.sidebar.write("✅ 진단 완료")
    else:
        st.sidebar.write("⬜ 진단 대기 중")

    if get_state(EDA_RESULT) is not None:
        st.sidebar.write("✅ EDA 완료")
    else:
        st.sidebar.write("⬜ EDA 대기 중")

    if get_state(KPI_RESULT) is not None:
        st.sidebar.write("✅ KPI 분석 완료")
    else:
        st.sidebar.write("⬜ KPI 분석 대기 중")

    if get_state(COHORT_RESULT) is not None:
        st.sidebar.write("✅ 코호트 분석 완료")
    else:
        st.sidebar.write("⬜ 코호트 분석 대기 중")
    
    if get_state(RFM_RESULT) is not None:
        st.sidebar.write("✅ RFM 분석 완료")
    else:
        st.sidebar.write("⬜ RFM 분석 대기 중")
    
    if get_state(PRODUCT_RESULT) is not None:
        st.sidebar.write("✅ 상품 분석 완료")
    else:
        st.sidebar.write("⬜ 상품 분석 대기 중")

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


if __name__ == "__main__":
    main()