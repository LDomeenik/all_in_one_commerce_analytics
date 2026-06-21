"""
cohort_page.py

코호트 분석 UI 페이지 모듈

기능:
    - 코호트 분석 실행 및 결과 출력
    - 코호트 retention matrix 히트맵 출력
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from core.analytics.cohort import run_cohort
from app.streamlit.session import (
    get_state,
    set_state,
    COLUMN_REGISTRY,
    PREPROCESSED_TABLES,
    DIAGNOSIS_RESULT,
    COHORT_RESULT
)


# render_cohort_page: 코호트 페이지 렌더링
def render_cohort_page():
    """
    코호트 분석 페이지를 렌더링합니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    st.subheader("코호트 분석")

    # column_registry 가져오기
    column_registry = get_state(COLUMN_REGISTRY)

    # 전처리 완료 여부 확인
    preprocessed_tables = get_state(PREPROCESSED_TABLES)

    if preprocessed_tables is None:
        st.warning("먼저 전처리를 완료해주세요.")
        return
    
    # 진단 결과에서 코호트 실행 가능 여부 확인
    diagnosis_result = get_state(DIAGNOSIS_RESULT)

    if diagnosis_result is not None and not diagnosis_result["cohort"]["available"]:
        st.error("Cohort 분석을 실행할 수 없습니다. 필수 컬럼을 확인해주세요.")
        st.write(f"누락된 필수 컬럼: {diagnosis_result['cohort']['missing_columns']}")
        return
    
    # 코호트 결과가 없으면 실행
    if get_state(COHORT_RESULT) is None:
        _run_cohort(preprocessed_tables, column_registry)
    
    # 있으면 기존 결과 출력
    else:
        _render_cohort_result()


# _run_cohort: 코호트 분석 실행 내장 함수
def _run_cohort(preprocessed_tables, column_registry):
    """
    코호트 분석을 실행하고 결과를 session_state에 저장합니다.

    Args:
        preprocessed_tables (dict[str, pd.DataFrame]): 전처리 완료 테이블 딕셔너리
        column_registry (dict[str, str]): {컬럼명: 테이블유형} 레지스트리
    
    Returns:
        없음
    
    Raises:
        없음
    """

    with st.spinner("Cohort 분석 중..."):
        try:
            cohort_result = run_cohort(preprocessed_tables, column_registry)
            set_state(COHORT_RESULT, cohort_result)
            st.rerun()

        except ValueError as e:
            st.error(f"Cohort 분석 중 오류가 발생했습니다: {e}")


# _render_cohort_result: 코호트 결과 출력 내장 함수
def _render_cohort_result():
    """
    코호트 분석 결과를 화면에 출력합니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    cohort_result = get_state(COHORT_RESULT)

    cohort_matrix = cohort_result["cohort_matrix"]
    retention_rate_matrix = cohort_result["retention_rate_matrix"]

    st.write("#### 코호트 Retention Rate (%)")

    # 코호트별 0월차 고객 수 (코호트 크기)
    cohort_sizes = cohort_matrix[0]

    # y축 레이블에 코호트 크기를 포함
    y_labels = [
        f"{month} ({int(cohort_sizes[month])}명)"
        for month in retention_rate_matrix.index
    ]

    # 히트맵 출력
    fig = px.imshow(
        retention_rate_matrix.fillna(0),
        labels=dict(x="경과 월 (Period)", y="", color="Retention (%)"),
        x=[f"{int(p)}월차" for p in retention_rate_matrix.columns],
        y=y_labels,
        color_continuous_scale="Blues",
        text_auto=".1f",
        aspect="auto"
    )

    fig.update_layout(
        xaxis=dict(side="top"),
        yaxis=dict(title=""),
        coloraxis_colorbar=dict(title="%")
    )

    st.plotly_chart(fig, use_container_width=True)

    # 절대값 matrix를 expander로 제공
    with st.expander("코호트별 실제 고객 수 보기"):
        st.dataframe(
            cohort_matrix.fillna(0).astype(int),
            use_container_width=True
        )

    # 재실행 출력
    if st.button("재실행"):
        set_state(COHORT_RESULT, None)
        st.rerun()