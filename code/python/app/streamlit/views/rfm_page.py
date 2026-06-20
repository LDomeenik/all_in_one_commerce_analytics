"""
rfm_page.py

RFM 분석 UI 페이지 모듈

기능:
    - RFM 분석 실행 및 결과 출력
    - 
"""


import streamlit as st
import pandas as pd
import plotly.express as px

from core.analytics.rfm import run_rfm
from app.streamlit.session import (
    get_state,
    set_state,
    PREPROCESSED_DF,
    DIAGNOSIS_RESULT,
    RFM_RESULT
)
from app.streamlit.constants import CHART_COLORS


# render_rfm_page: rfm 페이지 렌더링
def render_rfm_page():
    """
    RFM 분석 페이지를 렌더링합니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    st.subheader("RFM 분석")

    # 전처리 완료 여부 확인
    preprocessed_df = get_state(PREPROCESSED_DF)

    if preprocessed_df is None:
        st.warning("먼저 전처리를 완료해주세요.")
        return
    
    # 진단 결과에서 RFM 실행 가능 여부 확인
    diagnosis_result = get_state(DIAGNOSIS_RESULT)

    if diagnosis_result is not None and not diagnosis_result["rfm"]["available"]:
        st.error("RFM 분석을 실행할 수 없습니다. 필수 컬럼을 확인해주세요.")
        st.write(f"누락된 필수 컬럼: {diagnosis_result['rfm']['missing_columns']}")
        return
    
    # RFM 결과가 없으면 실행
    if get_state(RFM_RESULT) is None:
        _run_rfm(preprocessed_df)
    
    # 있으면 기존 결과 출력
    else:
        _render_rfm_result()


# _run_rfm: rfm 분석 실행 내장 함수
def _run_rfm(preprocessed_df):
    """
    RFM 분석을 실행하고 결과를 session_state에 저장합니다.

    Args:
        preprocessed_df (pd.DataFrame): 전처리 완료 DataFrame
    
    Returns:
        없음
    
    Raises:
        없음
    """

    with st.spinner("RFM 분석 중..."):
        try:
            rfm_result = run_rfm(preprocessed_df)
            set_state(RFM_RESULT, rfm_result)
            st.rerun()

        except ValueError as e:
            st.error(f"RFM 분석 중 오류가 발생했습니다: {e}")


# _render_rfm_result: RFM 결과 출력 내장 함수
def _render_rfm_result():
    """
    RFM 분석 결과를 화면에 출력합니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    rfm_result = get_state(RFM_RESULT)

    rfm_df = rfm_result["rfm_df"]
    segment_summary = rfm_result["segment_summary"]

    # 세그먼트별 고객 수 분포
    st.write("#### 세그먼트별 고객 수")

    fig = px.bar(
        segment_summary,
        x="segment",
        y="customer_count",
        # title="세그먼트별 고객 수",
        labels={"segment":"", "customer_count":""},
        color_discrete_sequence=[CHART_COLORS["customer"]]
    )

    fig.update_layout(
        hovermode="closest",
        showlegend=False,
        xaxis=dict(title=""),
        yaxis=dict(title="", tickformat=",")
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 세그먼트별 매출 비중
    st.write("#### 세그먼트별 매출 비중")

    fig = px.bar(
        segment_summary,
        x="segment",
        y="total_monetary",
        # title="세그먼트별 매출 비중",
        labels={"segment":"", "total_monetary":""},
        color_discrete_sequence=[CHART_COLORS["revenue"]]
    )

    fig.update_layout(
        hovermode="closest",
        showlegend=False,
        xaxis=dict(title=""),
        yaxis=dict(title="", tickformat=",")
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 세그먼트 요약 테이블
    st.write("#### 세그먼트 요약")

    st.dataframe(
        segment_summary,
        use_container_width=True
    )

    # 고객별 RFM 원본 데이터
    with st.expander("RFM 원본 데이터 보기"):
        st.dataframe(
            rfm_df,
            use_container_width=True
        )

    # 재실행 버튼
    if st.button("재실행"):
        set_state(RFM_RESULT, None)
        st.rerun()