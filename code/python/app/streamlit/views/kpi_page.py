"""
kpi_page.py

KPI 분석 UI 페이지 모듈

기능:
    - KPI 분석 실행 및 결과 출력
    - 매출 지표 출력
    - 주문 지표 출력
    - 고객 지표 출력
    - 월별 KPI 추이 차트 출력
"""


import streamlit as st
import pandas as pd
import plotly.express as px

from core.analytics.kpi import run_kpi
from app.streamlit.session import (
    get_state,
    set_state,
    PREPROCESSED_DF,
    DIAGNOSIS_RESULT,
    KPI_RESULT
)
from app.streamlit.constants import CHART_COLORS


# render_kpi_page: KPI 페이지 렌더링
def render_kpi_page():
    """
    KPI 분석 페이지를 렌더링합니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    st.subheader("KPI 분석")

    # 전처리 완료 여부 확인
    preprocessed_df = get_state(PREPROCESSED_DF)

    if preprocessed_df is None:
        st.warning("먼저 전처리를 완료해주세요.")
        return
    
    # 진단 결과에서 KPI 실행 가능 여부 확인
    diagnosis_result = get_state(DIAGNOSIS_RESULT)

    if diagnosis_result is not None and not diagnosis_result["kpi"]["available"]:
        st.error("KPI 분석을 실행할 수 없습니다. 필수 컬럼을 확인해주세요.")
        st.write(f"누락된 필수 컬럼: {diagnosis_result['kpi']['missing_columns']}")
        return
    
    # kpi 결과가 없으면 실행
    if get_state(KPI_RESULT) is None:
        _run_kpi(preprocessed_df)
    
    # 있으면 기존 결과 출력
    else:
        _render_kpi_result()


# _run_kpi: KPI 분석 실행 내장 함수
def _run_kpi(preprocessed_df):
    """
    KPI 분석을 실행하고 결과를 session_state에 저장합니다.

    Args:
        preprocessed_df (pd.DataFrame): 전처리 완료 DataFrame
    
    Returns:
        없음
    
    Raises:
        없음
    """

    with st.spinner("KPI 분석 중..."):
        try:
            kpi_result = run_kpi(preprocessed_df)
            set_state(KPI_RESULT, kpi_result)
            st.rerun()

        except ValueError as e:
            st.error(f"KPI 분석 중 오류가 발생했습니다: {e}")


# _render_kpi_result: KPI 결과 출력 내장 함수
def _render_kpi_result():
    """
    KPI 분석 결과를 화면에 출력합니다.

    Args:
        없음

    Returns:
        없음

    Raises:
        없음
    """

    kpi_result = get_state(KPI_RESULT)

    revenue_stats = kpi_result["revenue_stats"]
    order_stats = kpi_result["order_stats"]
    customer_stats = kpi_result["customer_stats"]
    monthly_trend = kpi_result["monthly_trend"]

    tab1, tab2, tab3 = st.tabs(["💰 매출", "📦 주문", "👥 고객"])

    with tab1:
        _render_revenue_tab(revenue_stats, monthly_trend)

    with tab2:
        _render_order_tab(order_stats, monthly_trend)

    with tab3:
        _render_customer_tab(customer_stats, monthly_trend)

    if st.button("재실행"):
        set_state(KPI_RESULT, None)
        st.rerun()


# _render_revenue_tab: 매출 탭 출력 내장 함수
def _render_revenue_tab(revenue_stats: dict, monthly_trend: pd.DataFrame):
    """
    매출 핵심 지표와 월별 매출 차트를 출력합니다.

    Args:
        revenue_stats (dict): 매출 지표
        monthly_trend (pd.DataFrame): 월별 KPI 추이

    Returns:
        없음

    Raises:
        없음
    """

    # 전체 기간 지표
    st.write("**전체 기간**")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("총 매출", f"{revenue_stats['total_revenue']:,.0f}")
    with col2:
        st.metric("순매출", f"{revenue_stats['net_revenue']:,.0f}")
    with col3:
        st.metric("AOV", f"{revenue_stats['aov']:,.2f}")

    # 당월 지표
    st.write("**당월**")
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "당월 매출",
            f"{revenue_stats['current_month_revenue']:,.0f}" if revenue_stats['current_month_revenue'] is not None else "데이터 없음",
            f"{revenue_stats['revenue_growth']:+.1f}%" if revenue_stats['revenue_growth'] is not None else None
        )
    with col2:
        st.metric(
            "당월 AOV",
            f"{revenue_stats['current_month_aov']:,.2f}" if revenue_stats['current_month_aov'] is not None else "데이터 없음"
        )

    st.divider()

    if monthly_trend.empty:
        st.info("월별 추이 데이터가 없습니다.")
        return

    # 월별 매출 차트
    if "revenue" in monthly_trend.columns:
        fig = px.line(
            monthly_trend,
            x="year_month",
            y="revenue",
            title="월별 매출",
            markers=True,
            labels={"year_month": "", "revenue": ""},
            color_discrete_sequence=[CHART_COLORS["revenue"]]
        )
        fig.update_traces(line=dict(width=2), marker=dict(size=8))
        fig.update_layout(
            hovermode="x unified",
            showlegend=False,
            xaxis=dict(type="category", title=""),
            yaxis=dict(title="", tickformat=",")
        )
        st.plotly_chart(fig, use_container_width=True)

    # 월별 AOV 차트
    if "aov" in monthly_trend.columns:
        fig = px.line(
            monthly_trend,
            x="year_month",
            y="aov",
            title="월별 AOV",
            markers=True,
            labels={"year_month": "", "aov": ""},
            color_discrete_sequence=[CHART_COLORS["aov"]]
        )
        fig.update_traces(line=dict(width=2), marker=dict(size=8))
        fig.update_layout(
            hovermode="x unified",
            showlegend=False,
            xaxis=dict(type="category", title=""),
            yaxis=dict(title="", tickformat=",")
        )
        st.plotly_chart(fig, use_container_width=True)


# _render_order_tab: 주문 탭 출력 내장 함수
def _render_order_tab(order_stats: dict, monthly_trend: pd.DataFrame):
    """
    주문 핵심 지표와 월별 주문 차트를 출력합니다.

    Args:
        order_stats (dict): 주문 지표
        monthly_trend (pd.DataFrame): 월별 KPI 추이

    Returns:
        없음

    Raises:
        없음
    """

    # 전체 기간 지표
    st.write("**전체 기간**")
    col1, col2 = st.columns(2)

    with col1:
        st.metric("총 주문 수", f"{order_stats['total_orders']:,}")
    with col2:
        st.metric(
            "취소율",
            f"{order_stats['cancel_rate']:.1f}%" if order_stats['cancel_rate'] is not None else "데이터 없음"
        )

    # 당월 지표
    st.write("**당월**")
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "당월 주문 수",
            f"{order_stats['current_month_orders']:,.0f}" if order_stats['current_month_orders'] is not None else "데이터 없음",
            f"{order_stats['order_growth']:+.1f}%" if order_stats['order_growth'] is not None else None
        )
    with col2:
        st.metric(
            "당월 취소율",
            f"{order_stats['current_month_cancel_rate']:.1f}%" if order_stats['current_month_cancel_rate'] is not None else "데이터 없음"
        )

    st.divider()

    if monthly_trend.empty:
        st.info("월별 추이 데이터가 없습니다.")
        return

    # 월별 주문 수 차트
    if "order_count" in monthly_trend.columns:
        fig = px.line(
            monthly_trend,
            x="year_month",
            y="order_count",
            title="월별 주문 수",
            markers=True,
            labels={"year_month": "", "order_count": ""},
            color_discrete_sequence=[CHART_COLORS["order"]]
        )
        fig.update_traces(line=dict(width=2), marker=dict(size=8))
        fig.update_layout(
            hovermode="x unified",
            showlegend=False,
            xaxis=dict(type="category", title=""),
            yaxis=dict(title="", tickformat=",")
        )
        st.plotly_chart(fig, use_container_width=True)

    # 월별 취소율 차트
    if "cancel_rate" in monthly_trend.columns:
        fig = px.line(
            monthly_trend,
            x="year_month",
            y="cancel_rate",
            title="월별 취소율",
            markers=True,
            labels={"year_month": "", "cancel_rate": ""},
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


# _render_customer_tab: 고객 탭 출력 내장 함수
def _render_customer_tab(customer_stats: dict, monthly_trend: pd.DataFrame):
    """
    고객 핵심 지표와 월별 고객 차트를 출력합니다.

    Args:
        customer_stats (dict): 고객 지표
        monthly_trend (pd.DataFrame): 월별 KPI 추이

    Returns:
        없음

    Raises:
        없음
    """

    if not customer_stats:
        st.info("customer_id 컬럼이 없어 고객 분석을 수행할 수 없습니다.")
        return

    # 전체 기간 지표
    st.write("**전체 기간**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총 고객 수", f"{customer_stats['total_customers']:,}")
    with col2:
        st.metric("신규 고객", f"{customer_stats['new_customers']:,}")
    with col3:
        st.metric("재구매 고객", f"{customer_stats['repeat_customers']:,}")
    with col4:
        st.metric("재구매율", f"{customer_stats['repeat_rate']:.1f}%")

    # 당월 지표
    st.write("**당월**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "당월 고객 수",
            f"{customer_stats['current_month_customers']:,.0f}" if customer_stats['current_month_customers'] is not None else "데이터 없음",
            f"{customer_stats['customer_growth']:+.1f}%" if customer_stats['customer_growth'] is not None else None
        )
    with col2:
        st.metric(
            "당월 신규 고객",
            f"{customer_stats['current_month_new_customers']:,.0f}" if customer_stats['current_month_new_customers'] is not None else "데이터 없음"
        )
    with col3:
        st.metric(
            "당월 재구매 고객",
            f"{customer_stats['current_month_repeat_customers']:,.0f}" if customer_stats['current_month_repeat_customers'] is not None else "데이터 없음"
        )
    with col4:
        st.metric(
            "당월 재구매율",
            f"{customer_stats['current_month_repeat_rate']:.1f}%" if customer_stats['current_month_repeat_rate'] is not None else "데이터 없음"
        )
    
    st.caption(
    "※ 신규 고객: 전체 기간 기준 1회 구매 고객 | "
    "재구매 고객: 전체 기간 기준 2회 이상 구매 고객"
    )

    st.divider()

    if monthly_trend.empty:
        st.info("월별 추이 데이터가 없습니다.")
        return

    # 월별 고객 수 차트
    if "customer_count" in monthly_trend.columns:
        fig = px.line(
            monthly_trend,
            x="year_month",
            y="customer_count",
            title="월별 고객 수",
            markers=True,
            labels={"year_month": "", "customer_count": ""},
            color_discrete_sequence=[CHART_COLORS["customer"]]
        )
        fig.update_traces(line=dict(width=2), marker=dict(size=8))
        fig.update_layout(
            hovermode="x unified",
            showlegend=False,
            xaxis=dict(type="category", title=""),
            yaxis=dict(title="", tickformat=",")
        )
        st.plotly_chart(fig, use_container_width=True)

    # 월별 신규 / 재구매 고객 차트
    if "new_customers" in monthly_trend.columns and "repeat_customers" in monthly_trend.columns:
        fig = px.line(
            monthly_trend,
            x="year_month",
            y=["new_customers", "repeat_customers"],
            title="월별 신규 / 재구매 고객 수",
            markers=True,
            labels={"year_month": "", "value": "", "variable": "구분"},
            color_discrete_map={
                "new_customers": CHART_COLORS["order"],
                "repeat_customers": CHART_COLORS["customer"]
            }
        )
        fig.update_traces(line=dict(width=2), marker=dict(size=8))
        fig.update_layout(
            hovermode="x unified",
            xaxis=dict(type="category", title=""),
            yaxis=dict(title="", tickformat=",")
        )
        fig.for_each_trace(lambda t: t.update(
            name="신규 고객" if t.name == "new_customers" else "재구매 고객"
        ))
        st.plotly_chart(fig, use_container_width=True)

    # 월별 재구매율 차트
    if "repeat_rate" in monthly_trend.columns:
        fig = px.line(
            monthly_trend,
            x="year_month",
            y="repeat_rate",
            title="월별 재구매율",
            markers=True,
            labels={"year_month": "", "repeat_rate": ""},
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