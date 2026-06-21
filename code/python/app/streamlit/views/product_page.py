"""
product_page.py

상품 분석 UI 페이지 모듈

기능:
    - 상품 분석 실행 및 결과 출력 (탭 1)
    - 카테고리 분석 실행 및 결과 출력 (탭 2)
    - 매출 집중도 요약 지표
    - 매출/판매량 기준 Top N 상품 차트
    - 카테고리별 매출, 판매량, 상품 수, AOV, 매출 비율
"""


import streamlit as st
import pandas as pd
import plotly.express as px

from core.analytics.product import run_product
from core.analytics.category import run_category
from app.streamlit.session import (
    get_state,
    set_state,
    COLUMN_REGISTRY,
    PREPROCESSED_TABLES,
    DIAGNOSIS_RESULT,
    PRODUCT_RESULT,
    CATEGORY_RESULT
)
from app.streamlit.constants import CHART_COLORS


# render_product_page: 상품 분석 페이지 렌더링
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

    # column_registry 가져오기
    column_registry = get_state(COLUMN_REGISTRY)

    # 전처리 완료 여부 확인
    preprocessed_tables = get_state(PREPROCESSED_TABLES)

    if preprocessed_tables is None:
        st.warning("먼저 전처리를 완료해주세요.")
        return

    # 진단 결과에서 상품 분석 실행 가능 여부 확인
    diagnosis_result = get_state(DIAGNOSIS_RESULT)

    if diagnosis_result is not None and not diagnosis_result["product"]["available"]:
        st.error("상품 분석을 실행할 수 없습니다. 필수 컬럼을 확인해주세요.")
        st.write(f"누락된 필수 컬럼: {diagnosis_result['product']['missing_columns']}")
        return

    # 탭 구성
    tab1, tab2 = st.tabs(["🛍️ 상품별 분석", "📂 카테고리별 분석"])

    with tab1:
        _render_product_tab(preprocessed_tables, diagnosis_result, column_registry)

    with tab2:
        _render_category_tab(preprocessed_tables, diagnosis_result, column_registry)


# _render_product_tab: 상품별 분석 탭 렌더링
def _render_product_tab(preprocessed_tables, diagnosis_result, column_registry):
    """
    상품별 분석 탭을 렌더링합니다.

    Args:
        preprocessed_tables (dict[str, pd.DataFrame]): 전처리 완료 테이블 딕셔너리
        diagnosis_result (dict): 진단 결과
        column_registry (dict[str, str]): {컬럼명: 테이블유형} 레지스트리

    Returns:
        없음

    Raises:
        없음
    """

    if get_state(PRODUCT_RESULT) is None:
        _run_product(preprocessed_tables, column_registry)
    else:
        _render_product_result()


# _render_category_tab: 카테고리별 분석 탭 렌더링
def _render_category_tab(preprocessed_tables, diagnosis_result, column_registry):
    """
    카테고리별 분석 탭을 렌더링합니다.

    Args:
        preprocessed_tables (dict[str, pd.DataFrame]): 전처리 완료 테이블 딕셔너리
        diagnosis_result (dict): 진단 결과
        column_registry (dict[str, str]): {컬럼명: 테이블유형} 레지스트리

    Returns:
        없음

    Raises:
        없음
    """

    # 카테고리 분석 가능 여부 체크
    if diagnosis_result is not None and not diagnosis_result["category"]["available"]:
        st.info("카테고리 데이터가 없어 분석을 수행할 수 없습니다.")
        st.write(f"누락된 필수 컬럼: {diagnosis_result['category']['missing_columns']}")
        return

    if get_state(CATEGORY_RESULT) is None:
        _run_category(preprocessed_tables, column_registry)
    else:
        _render_category_result()


# _run_product: 상품 분석 실행
def _run_product(preprocessed_tables, column_registry):
    """
    상품 분석을 실행하고 결과를 session_state 에 저장합니다.

    Args:
        preprocessed_tables (dict[str, pd.DataFrame]): 전처리 완료 테이블 딕셔너리
        column_registry (dict[str, str]): {컬럼명: 테이블유형} 레지스트리

    Returns:
        없음

    Raises:
        없음
    """

    with st.spinner("상품 분석 중..."):
        try:
            product_result = run_product(preprocessed_tables, column_registry)
            set_state(PRODUCT_RESULT, product_result)
            st.rerun()
        except ValueError as e:
            st.error(f"상품 분석 중 오류가 발생했습니다: {e}")


# _run_category: 카테고리 분석 실행
def _run_category(preprocessed_tables, column_registry):
    """
    카테고리 분석을 실행하고 결과를 session_state 에 저장합니다.

    Args:
        preprocessed_tables (dict[str, pd.DataFrame]): 전처리 완료 테이블 딕셔너리
        column_registry (dict[str, str]): {컬럼명: 테이블유형} 레지스트리

    Returns:
        없음

    Raises:
        없음
    """

    with st.spinner("카테고리 분석 중..."):
        try:
            category_result = run_category(preprocessed_tables, column_registry)
            set_state(CATEGORY_RESULT, category_result)
            st.rerun()
        except ValueError as e:
            st.error(f"카테고리 분석 중 오류가 발생했습니다: {e}")


# _render_product_result: 상품 분석 결과 출력
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
        st.metric("전체 매출", f"{concentration['total_revenue']:,.0f}")

    with col3:
        st.metric(
            "Top 3 집중도",
            f"{concentration['top3_revenue_pct']:.1f}%" if concentration['top3_revenue_pct'] is not None else "N/A"
        )

    with col4:
        st.metric(
            "Top 5 집중도",
            f"{concentration['top5_revenue_pct']:.1f}%" if concentration['top5_revenue_pct'] is not None else "N/A"
        )

    with col5:
        st.metric(
            "Top 10 집중도",
            f"{concentration['top10_revenue_pct']:.1f}%" if concentration['top10_revenue_pct'] is not None else "N/A"
        )

    st.divider()

    # Top N 설정
    st.write(f"#### Top N 설정")

    n = st.radio(
        "상품 개수 기준을 선택하세요.",
        options=[3, 5, 10, 20],
        index=2,
        horizontal=True,
        key="product_top_n"
    )

    # 매출 기준 Top N 상품 차트
    st.write(f"#### 매출 기준 Top {n} 상품")

    top_revenue = product_summary.sort_values("total_revenue", ascending=False).head(n)
    x_col = "product_name" if "product_name" in top_revenue.columns else "product_id"

    fig = px.bar(
        top_revenue,
        x=x_col,
        y="total_revenue",
        # title=f"매출 기준 Top {n} 상품",
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
    st.write(f"#### 판매량 기준 Top {n} 상품")

    if "total_quantity" in product_summary.columns:
        top_quantity = product_summary.sort_values("total_quantity", ascending=False).head(n)
        fig = px.bar(
            top_quantity,
            x=x_col,
            y="total_quantity",
            # title=f"판매량 기준 Top {n} 상품",
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
    if st.button("재실행", key="product_rerun"):
        set_state(PRODUCT_RESULT, None)
        st.rerun()


# _render_category_result: 카테고리 분석 결과 출력
def _render_category_result():
    """
    카테고리 분석 결과를 화면에 출력합니다.

    Args:
        없음

    Returns:
        없음

    Raises:
        없음
    """

    category_result = get_state(CATEGORY_RESULT)
    category_summary = category_result["category_summary"]

    # 카테고리별 매출 차트
    st.write("#### 카테고리별 매출")

    fig = px.bar(
        category_summary,
        x="product_category",
        y="total_revenue",
        # title="카테고리별 매출",
        labels={"product_category": "", "total_revenue": ""},
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

    # 카테고리별 매출 비율 차트
    st.write("#### 카테고리별 매출 비율")

    fig = px.pie(
        category_summary,
        names="product_category",
        values="total_revenue",
        # title="카테고리별 매출 비율"
    )

    fig.update_layout(showlegend=True)

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 카테고리별 판매량 차트
    if "total_quantity" in category_summary.columns:
        st.write("#### 카테고리별 판매량")

        fig = px.bar(
            category_summary,
            x="product_category",
            y="total_quantity",
            # title="카테고리별 판매량",
            labels={"product_category": "", "total_quantity": ""},
            color_discrete_sequence=[CHART_COLORS["order"]]
        )

        fig.update_layout(
            hovermode="closest",
            showlegend=False,
            xaxis=dict(title=""),
            yaxis=dict(title="", tickformat=",")
        )

        st.plotly_chart(fig, use_container_width=True)

        st.divider()

    # 카테고리 요약 테이블
    st.write("#### 카테고리 요약")
    st.dataframe(category_summary, use_container_width=True)

    # 재실행 버튼
    if st.button("재실행", key="category_rerun"):
        set_state(CATEGORY_RESULT, None)
        st.rerun()