"""
delivery_page.py

배송/운영 분석 UI 페이지 모듈

기능:
    - 배송/운영 분석 실행 및 결과 출력
    - 핵심 배송 지표 출력
    - 배송 소요일 구간별 분포 차트
    - 월별 배송 추이 차트
"""


from tkinter import DISABLED

import streamlit as st
import pandas as pd
import plotly.express as px

from core.analytics.delivery import run_delivery
from app.streamlit.session import (
    get_state,
    set_state,
    COLUMN_REGISTRY,
    PREPROCESSED_TABLES,
    DIAGNOSIS_RESULT,
    DELIVERY_RESULT,
    ANALYSIS_STATUS
)
from app.streamlit.constants import CHART_COLORS


# render_delivery_page: 배송/운영 분석 페이지 렌더링
def render_delivery_page():
    """
    배송/운영 분석 페이지를 렌더링합니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    st.subheader("배송/운영 분석")

    # column_registry 가져오기
    column_registry = get_state(COLUMN_REGISTRY)

    # 전처리 완료 여부 확인
    preprocessed_tables = get_state(PREPROCESSED_TABLES)

    if preprocessed_tables is None:
        st.warning("먼저 전처리를 완료해주세요.")
        return

    # 진단 결과에서 배송 분석 실행 가능 여부 확인
    diagnosis_result = get_state(DIAGNOSIS_RESULT)

    if diagnosis_result is not None and not diagnosis_result["delivery"]["available"]:
        st.error("배송 분석을 실행할 수 없습니다. 필수 컬럼을 확인해주세요.")
        st.write(f"누락된 필수 컬럼: {diagnosis_result['delivery']['missing_columns']}")
        return
    
    # 배송 분석 결과가 없으면 실행
    if get_state(DELIVERY_RESULT) is None:
        _run_delivery(preprocessed_tables, column_registry)
    
    # 있으면 기존 결과 출력
    else:
        _render_delivery_result()


# _run_delivery: 배송 분석 실행 내장 함수
def _run_delivery(preprocessed_tables, column_registry):
    """
    배송 분석을 실행하고 결과를 session_state에 저장합니다.

    Args:
        preprocessed_tables (dict[str, pd.DataFrame]): 전처리 완료 테이블 딕셔너리
        column_registry (dict[str, str]): {컬럼명: 테이블유형} 레지스트리
    
    Returns:
        없음
    
    Raises:
        없음
    """

    with st.spinner("배송 분석 중..."):
        try:
            delivery_result = run_delivery(preprocessed_tables, column_registry)

            # 분석 성공 상태 저장
            analysis_status = get_state(ANALYSIS_STATUS) or {}
            analysis_status["delivery"] = "success"

            set_state(DELIVERY_RESULT, delivery_result)
            set_state(ANALYSIS_STATUS, analysis_status)

            st.rerun()

        except ValueError as e:
            # 분석 실패 상태 저장
            analysis_status = get_state(ANALYSIS_STATUS) or {}
            analysis_status["delivery"] = "failed"

            set_state(ANALYSIS_STATUS, analysis_status)

            st.error(f"배송 분석 중 오류가 발생했습니다: {e}")


# _render_delivery_result: 배송 분석 결과 출력 내장 함수
def _render_delivery_result():
    """
    배송 분석 결과를 화면에 출력합니다.

    Args:
        없음

    Returns:
        없음

    Raises:
        없음
    """

    delivery_result = get_state(DELIVERY_RESULT)

    delivery_stats = delivery_result["delivery_stats"]
    delivery_distribution = delivery_result["delivery_distribution"]
    monthly_delivery = delivery_result["monthly_delivery"]

    # 핵심 배송 지표
    st.write("#### 핵심 배송 지표")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "평균 배송 소요일",
            f"{delivery_stats['avg_total_lead_time']:.1f}일"
        )
    with col2:
        st.metric(
            "평균 출고 리드타임",
            f"{delivery_stats['avg_shipping_lead_time']:.1f}일" if delivery_stats['avg_shipping_lead_time'] is not None else "N/A"
        )
        if delivery_stats['avg_shipping_lead_time'] is None:
            st.caption("※ shipped_date 컬럼 없음")
    with col3:
        st.metric(
            "평균 배송 리드타임",
            f"{delivery_stats['avg_delivery_lead_time']:.1f}일" if delivery_stats['avg_delivery_lead_time'] is not None else "N/A"
        )
        if delivery_stats['avg_delivery_lead_time'] is None:
            st.caption("※ delivery_days 컬럼 없음")
    with col4:
        st.metric(
            "배송 완료율",
            f"{delivery_stats['delivery_complete_rate']:.1f}%" if delivery_stats['delivery_complete_rate'] is not None else "N/A"
        )
        if delivery_stats['delivery_complete_rate'] is None:
            st.caption("※ order_status 컬럼 없음")
    with col5:
        st.metric(
            "배송 지연율",
            f"{delivery_stats['delivery_delay_rate']:.1f}%" if delivery_stats['delivery_delay_rate'] is not None else "N/A"
        )
        if delivery_stats['delivery_delay_rate'] is None:
            st.caption("※ estimated_delivery_date 컬럼 없음")

    st.divider()

    # 배송 소요일 구간별 분포
    st.write("#### 배송 소요일 분포")

    fig = px.bar(
        delivery_distribution,
        x="range",
        y="order_count",
        title="배송 소요일 구간별 주문 수",
        labels={"range": "", "order_count": ""},
        text="pct",
        color_discrete_sequence=[CHART_COLORS["delivery"]]
    )
    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )
    fig.update_layout(
        hovermode="closest",
        showlegend=False,
        xaxis=dict(title=""),
        yaxis=dict(title="", tickformat=",")
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 월별 배송 소요일 추이
    st.write("#### 월별 배송 추이")

    fig = px.line(
        monthly_delivery,
        x="year_month",
        y="avg_lead_time",
        title="월별 평균 배송 소요일",
        markers=True,
        labels={"year_month": "", "avg_lead_time": ""},
        color_discrete_sequence=[CHART_COLORS["delivery"]]
    )
    fig.update_traces(line=dict(width=2), marker=dict(size=8))
    fig.update_layout(
        hovermode="x unified",
        showlegend=False,
        xaxis=dict(type="category", title=""),
        yaxis=dict(title="", tickformat=".1f", ticksuffix="일")
    )
    st.plotly_chart(fig, use_container_width=True)

    # 월별 배송 지연율 추이 (있는 경우)
    if "delay_rate" in monthly_delivery.columns:
        fig = px.line(
            monthly_delivery,
            x="year_month",
            y="delay_rate",
            title="월별 배송 지연율",
            markers=True,
            labels={"year_month": "", "delay_rate": ""},
            color_discrete_sequence=[CHART_COLORS["rate"]]
        )
        fig.update_traces(line=dict(width=2), marker=dict(size=8))
        fig.update_layout(
            hovermode="x unified",
            showlegend=False,
            xaxis=dict(type="category", title=""),
            yaxis=dict(title="", tickformat=".1f", ticksuffix="%")
        )
        st.plotly_chart(fig, use_container_width=True)

    # 재실행 버튼
    if st.button("재실행"):
        analysis_status = get_state(ANALYSIS_STATUS) or {}
        analysis_status.pop("delivery", None)

        set_state(DELIVERY_RESULT, None)
        set_state(ANALYSIS_STATUS, analysis_status)

        st.rerun()