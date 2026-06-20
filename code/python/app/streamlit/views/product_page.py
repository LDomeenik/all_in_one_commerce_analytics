"""
product_page.py

상품 분석 UI 페이지 모듈

기능:
    - 상품 분석 실행 및 결과 출력
    - 매출 집중도 요약 지표
    - 매출 기준 Top N 상품 차트
    - 판매량 기준 Top N 상품 차트
    - 전체 상품 요약 테이블
"""


import streamlit as st
import pandas as pd
import plotly.express as px

from core.analytics.product import run_product
from app.streamlit.session import (
    get_state,
    set_state,
    PREPROCESSED_DF,
    DIAGNOSIS_RESULT,
    PRODUCT_RESULT
)
from app.streamlit.constants import CHART_COLORS


# render_product_page: 상품 페이지 렌더링
def render_product_page():
    """
    상품 분석 페이지를 렌더링합니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    st.subheader("상품 분석")

    # 전처리 완료 여부 확인
    preprocessed_df = get_state(PREPROCESSED_DF)

    if preprocessed_df is None:
        st.warning("먼저 전처리를 완료해주세요.")
        return
    
    # 진단 결과에서 상품 분석 실행 가능 여부 확인
    diagnosis_result = get_state(DIAGNOSIS_RESULT)

    if diagnosis_result is not None and not diagnosis_result["product"]["available"]:
        st.error("상품 분석을 실행할 수 없습니다. 필수 컬럼을 확인해주세요.")
        st.write(f"누락된 필수 컬럼: {diagnosis_result['product']['missing_columns']}")
        return
    
    # 상품 분석 결과가 없으면 실행
    if get_state(PRODUCT_RESULT) is None:
        _run_product(preprocessed_df)
    
    # 있으면 기존 결과 출력
    else:
        _render_product_result()


# _run_product: 상품 분석 실행 내장 함수
def _run_product(preprocessed_df):
    """
    상품 분석을 실행하고 결과를 PRODUCT_RESULT에 저장합니다.

    Args:
        preprocessed_df (pd.DataFrame): 전처리 완료 데이터프레임
    
    Returns:
        없음
    
    Raises:
        없음
    """

    with st.spinner("상품 분석 중..."):
        try:
            product_result = run_product(preprocessed_df)
            set_state(PRODUCT_RESULT, product_result)
            st.rerun()

        except ValueError as e:
            st.error(f"상품 분석 중 오류가 발생했습니다: {e}")


# _render_product_result: 상품 분석 결과 출력 내장 함수
def _render_product_result():
    """
    상품 분석 결과를 화면에 출력합니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    product_result = get_state(PRODUCT_RESULT)

    product_summary = product_result["product_summary"]
    top_products = product_result["top_products"]
    concentration = product_result["concentration"]

    # 매출 집중도 요약 지표
    st.write("#### 매출 집중도")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("전체 상품 수", f"{concentration['total_products']:,}")
    
    with col2:
        st.metric("전체 매출 수", f"{concentration['total_revenue']:,.0f}")
    
    with col3:
        st.metric(
            "Top 3 집중도", f"{concentration['top3_revenue_pct']:.1f}%" 
            if concentration['top3_revenue_pct'] is not None else "N/A"
        )
    
    with col4:
        st.metric(
            "Top 5 집중도", f"{concentration['top5_revenue_pct']:.1f}%"
            if concentration['top5_revenue_pct'] is not None else "N/A"
        )
    
    with col5:
        st.metric(
            "Top 10 집중도",
            f"{concentration['top10_revenue_pct']:.1f}%"
            if concentration['top10_revenue_pct'] is not None else "N/A"
        )

    st.divider()

    # Top N 설정
    st.write("#### Top N 설정")
    n = st.radio(
        "상품 개수 기준을 선택하세요.",
        options=[3, 5, 10, 20],
        index=2,
        horizontal=True
    )

    # 매출 기준 Top N 상품 차트
    st.write("#### 매출 기준 Top N 상품")

    top_revenue = product_summary.sort_values("total_revenue", ascending=False).head(n)
    x_col = "product_name" if "product_name" in top_revenue.columns else "product_id"

    fig = px.bar(
        top_revenue,
        x=x_col,
        y="total_revenue",
        title=f"매출 기준 Top {n} 상품",
        labels={x_col: "", "total_revenue": ""},
        color_discrete_sequence=[CHART_COLORS["revenue"]]
    )

    fig.update_layout(
        hovermode="closest",
        showlegend=False,
        xaxis=dict(title=""),
        yaxis=dict(title="", tickformat=",")
    )

    st.plotly_chart(fig, use_container_width=True)

    # 판매량 기준 Top N 상품 차트
    st.write("#### 판매량 기준 Top N 상품")

    if "total_quantity" in product_summary.columns:
        top_quantity = product_summary.sort_values("total_quantity", ascending=False).head(n)

        fig = px.bar(
            top_quantity,
            x=x_col,
            y="total_quantity",
            title=f"판매량 기준 Top {n} 상품",
            labels={x_col: "", "total_quantity": ""},
            color_discrete_sequence=[CHART_COLORS["order"]]
        )

        fig.update_layout(
            hovermode="closest",
            showlegend=False,
            xaxis=dict(title=""),
            yaxis=dict(title="", tickformat=",")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("quantity 컬럼이 없어 판매량 분석을 수행할 수 없습니다.")

    # 전체 상품 요약 테이블
    with st.expander("전체 상품 요약 보기"):
        st.dataframe(product_summary, use_container_width=True)

    # 재실행 버튼
    if st.button("재실행"):
        set_state(PRODUCT_RESULT, None)
        st.rerun()