"""
sidebar.py

Streamlit 사이드바 UI 모듈

기능:
    - 페이지 네비게이션 구성
    - 전체 진행 상태 표시
    - 분석 모듈별 완료 / 실패 / 불가 / 대기 상태 표시
"""

import streamlit as st

from app.streamlit.session import (
    get_state,
    TABLES,
    CONFIRMED_MAPPING,
    PREPROCESSED_TABLES,
    DIAGNOSIS_RESULT,
    EDA_RESULT,
    KPI_RESULT,
    COHORT_RESULT,
    RFM_RESULT,
    PRODUCT_RESULT,
    DELIVERY_RESULT,
    ANALYSIS_STATUS
)


# _render_basic_progress_status: 기본 진행 상태 표시
def _render_basic_progress_status(label: str, state_key: str):
    """
    업로드, 매핑, 전처리, 진단처럼 단순 완료/대기 상태를 표시합니다.

    Args:
        label (str): 사이드바에 표시할 단계 이름
        state_key (str): 확인할 session_state 키

    Returns:
        없음

    Raises:
        없음
    """

    state = get_state(state_key)

    if state:
        st.sidebar.write(f"✅ {label} 완료")
    else:
        st.sidebar.write(f"⬜ {label} 대기 중")


# _render_analysis_progress_status: 분석 모듈 진행 상태 표시
def _render_analysis_progress_status(
    label: str,
    result_key: str,
    module_key: str
):
    """
    분석 모듈의 진행 상태를 표시합니다.

    상태 기준:
        - 결과 있음: 완료
        - 진단 결과 기준 실행 불가: 분석 불가
        - 실행 중 예외 발생: 분석 실패
        - 그 외: 대기 중

    Args:
        label (str): 사이드바에 표시할 분석 이름
        result_key (str): 분석 결과 session_state 키
        module_key (str): diagnosis_result / analysis_status에서 사용하는 분석 키

    Returns:
        없음

    Raises:
        없음
    """

    result = get_state(result_key)
    diagnosis_result = get_state(DIAGNOSIS_RESULT)
    analysis_status = get_state(ANALYSIS_STATUS) or {}

    # 분석 결과가 있으면 완료
    if result is not None:
        st.sidebar.write(f"✅ {label} 완료")
        return

    # 분석 실행 중 오류가 발생한 경우
    if analysis_status.get(module_key) == "failed":
        st.sidebar.write(f"❌ {label} 분석 실패")
        return

    # 진단 결과상 실행 불가인 경우
    if (
        diagnosis_result is not None
        and module_key in diagnosis_result
        and not diagnosis_result[module_key]["available"]
    ):
        st.sidebar.write(f"🚫 {label} 분석 불가")
        return

    # 아직 실행 전
    st.sidebar.write(f"⬜ {label} 대기 중")


# render_sidebar: 사이드바 렌더링
def render_sidebar() -> str:
    """
    사이드바 네비게이션 및 진행 상태를 렌더링합니다.

    Args:
        없음

    Returns:
        str: 선택된 페이지 이름

    Raises:
        없음
    """

    st.sidebar.title("📊 Commerce Analytics")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "페이지 선택",
        options=[
            "데이터 업로드",
            "컬럼 매핑",
            "전처리",
            "진단",
            "EDA",
            "KPI",
            "Cohort",
            "RFM",
            "상품",
            "배송/운영"
        ],
        index=0
    )

    st.sidebar.divider()

    st.sidebar.write("#### 진행 상태")

    # 기본 처리 단계
    _render_basic_progress_status("데이터 업로드", TABLES)
    _render_basic_progress_status("컬럼 매핑", CONFIRMED_MAPPING)
    _render_basic_progress_status("전처리", PREPROCESSED_TABLES)
    _render_basic_progress_status("진단", DIAGNOSIS_RESULT)

    # 분석 모듈 단계
    _render_analysis_progress_status("EDA", EDA_RESULT, "eda")
    _render_analysis_progress_status("KPI", KPI_RESULT, "kpi")
    _render_analysis_progress_status("코호트", COHORT_RESULT, "cohort")
    _render_analysis_progress_status("RFM", RFM_RESULT, "rfm")
    _render_analysis_progress_status("상품", PRODUCT_RESULT, "product")
    _render_analysis_progress_status("배송/운영", DELIVERY_RESULT, "delivery")

    return page