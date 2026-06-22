"""
eda_page.py

EDA 분석 UI 페이지 모듈

기능:
    - EDA 분석 실행 및 결과 출력
    - 테이블별 탭 구분 출력
    - 기초 통계 출력
    - 수치형 컬럼 통계 출력
    - 문자열 컬럼 통계 출력
    - 시계열 분포 차트 출력
    - 주요 컬럼 분포 차트 출력
"""


import streamlit as st
import pandas as pd
import plotly.express as px

from core.analytics.eda import run_eda
from app.streamlit.session import (
    get_state,
    set_state,
    COLUMN_REGISTRY,
    PREPROCESSED_TABLES,
    DIAGNOSIS_RESULT,
    EDA_RESULT,
    ANALYSIS_STATUS
)
from app.streamlit.constants import CHART_COLORS


# render_eda_page: EDA 페이지 렌더링
def render_eda_page():
    """
    EDA 분석 페이지를 렌더링합니다.

    Args:
        없음

    Returns:
        없음

    Raises:
        없음
    """

    st.subheader("EDA (탐색적 데이터 분석)")

    # column_registry 가져오기
    column_registry = get_state(COLUMN_REGISTRY)

    # 전처리 완료 여부 확인
    preprocessed_tables = get_state(PREPROCESSED_TABLES)

    if preprocessed_tables is None:
        st.warning("먼저 전처리를 완료해주세요.")
        return

    # 진단 결과에서 EDA 실행 가능 여부 확인
    diagnosis_result = get_state(DIAGNOSIS_RESULT)

    if diagnosis_result is not None and not diagnosis_result["eda"]["available"]:
        st.error("EDA 분석을 실행할 수 없습니다. 필수 컬럼을 확인해주세요.")
        st.write(f"누락된 필수 컬럼: {diagnosis_result['eda']['missing_columns']}")
        return

    # EDA 결과가 없으면 실행
    # 있으면 바로 결과 출력
    if get_state(EDA_RESULT) is None:
        _run_eda(preprocessed_tables, column_registry)
    else:
        _render_eda_result()


# _run_eda: EDA 분석 실행 내장 함수
def _run_eda(preprocessed_tables, column_registry):
    """
    EDA 분석을 실행하고 결과를 session_state 에 저장합니다.

    Args:
        preprocessed_tables (dict[str, pd.DataFrame]): 전처리 완료 테이블 딕셔너리
        column_registry (dict[str, str]): {컬럼명: 테이블유형} 레지스트리

    Returns:
        없음

    Raises:
        없음
    """

    with st.spinner("EDA 분석 중..."):
        try:
            eda_result = run_eda(preprocessed_tables, column_registry)

            # 분석 성공 상태 저장
            analysis_status = get_state(ANALYSIS_STATUS) or {}
            analysis_status["eda"] = "success"

            set_state(EDA_RESULT, eda_result)
            set_state(ANALYSIS_STATUS, analysis_status)

            st.rerun()

        except ValueError as e:
            # 분석 실패 상태 저장
            analysis_status = get_state(ANALYSIS_STATUS) or {}
            analysis_status["eda"] = "failed"

            set_state(ANALYSIS_STATUS, analysis_status)

            st.error(f"EDA 분석 중 오류가 발생했습니다: {e}")


# _get_ordered_table_types: EDA 탭 출력 순서 반환
def _get_ordered_table_types(eda_result: dict) -> list:
    """
    EDA 결과의 테이블 타입을 지정된 우선순위에 따라 정렬합니다.

    우선순위:
        1. customer
        2. order_item
        3. order
        4. 기타 테이블

    Args:
        eda_result (dict): EDA 분석 결과

    Returns:
        list: 정렬된 테이블 타입 리스트

    Raises:
        없음
    """

    priority = ["order", "order_item", "customer"]

    ordered = [
        table_type
        for table_type in priority
        if table_type in eda_result
    ]

    others = [
        table_type
        for table_type in eda_result.keys()
        if table_type not in priority
    ]

    return ordered + others


# _render_eda_result: EDA 결과 출력 내장 함수
def _render_eda_result():
    """
    EDA 분석 결과를 화면에 출력합니다.

    Args:
        없음

    Returns:
        없음

    Raises:
        없음
    """

    eda_result = get_state(EDA_RESULT)

    if not eda_result:
        st.warning("EDA 결과가 없습니다. 다시 실행해주세요.")
        return

    table_types = _get_ordered_table_types(eda_result)

    tab_labels = [
        f"{_get_table_icon(table_type)} {table_type}"
        for table_type in table_types
    ]

    tabs = st.tabs(tab_labels)

    for tab, table_type in zip(tabs, table_types):
        with tab:
            table_result = eda_result[table_type]
            _render_single_table_eda(table_type, table_result)

    # 재실행 버튼
    st.divider()

    if st.button("재실행"):
        analysis_status = get_state(ANALYSIS_STATUS) or {}
        analysis_status.pop("eda", None)

        set_state(EDA_RESULT, None)
        set_state(ANALYSIS_STATUS, analysis_status)

        st.rerun()


# _get_table_icon: 테이블 타입별 아이콘 반환
def _get_table_icon(table_type: str) -> str:
    """
    테이블 타입에 맞는 아이콘을 반환합니다.

    Args:
        table_type (str): 테이블 타입

    Returns:
        str: 아이콘 문자열

    Raises:
        없음
    """

    icon_map = {
        "customer": "👥",
        "order_item": "🧾",
        "order": "📦",
        "product": "🛍️",
        "payment": "💳",
        "delivery": "🚚"
    }

    return icon_map.get(table_type, "📄")


# _render_single_table_eda: 단일 테이블 EDA 결과 출력
def _render_single_table_eda(table_type: str, table_result: dict):
    """
    단일 테이블의 EDA 결과를 출력합니다.

    Args:
        table_type (str): 테이블 타입
        table_result (dict): 단일 테이블 EDA 결과

    Returns:
        없음

    Raises:
        없음
    """

    st.write(f"### {table_type} 테이블")

    # 기초 통계 출력
    _render_basic_stats(table_result["basic_stats"])
    st.divider()

    # 시계열 분포 차트 출력
    _render_time_series(table_result["time_series"], table_type)
    st.divider()

    # 주요 컬럼 분포 차트 출력
    _render_distribution(table_result["distribution"], table_type)
    st.divider()

    # 수치형 / 문자열 컬럼 통계 출력
    _render_column_stats(
        table_result["numeric_stats"],
        table_result["categorical_stats"]
    )


# _render_basic_stats: 기초 통계 출력 내장 함수
def _render_basic_stats(basic_stats: dict):
    """
    기초 통계 정보를 출력합니다.

    Args:
        basic_stats (dict): 기초 통계 정보

    Returns:
        없음

    Raises:
        없음
    """

    st.write("#### 기초 통계")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("전체 행 수", f"{basic_stats['row_count']:,}")

    with col2:
        st.metric("컬럼 수", basic_stats["column_count"])

    with col3:
        date_range = basic_stats.get("date_range", {})

        if date_range:
            st.metric(
                "분석 기간",
                f"{date_range['start']} - {date_range['end']}",
                f"{date_range['days']}일"
            )
        else:
            st.metric("분석 기간", "N/A")


# _render_time_series: 시계열 분포 차트 출력 내장 함수
def _render_time_series(time_series: pd.DataFrame, table_type: str = ""):
    """
    월별 주문 수 및 매출 추이 차트를 출력합니다.

    Args:
        time_series (pd.DataFrame): 시계열 집계 결과
        table_type (str): 테이블 타입 (plotly_chart key 중복 방지용)

    Returns:
        없음

    Raises:
        없음
    """

    st.write("#### 월별 추이")

    if time_series.empty:
        st.info("order_date 컬럼이 없어 시계열 분석을 수행할 수 없습니다.")
        return

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(
            time_series,
            x="year_month",
            y="order_count",
            title="월별 주문 수",
            markers=True,
            labels={"year_month": "", "order_count": "건"},
            color_discrete_sequence=[CHART_COLORS["order"]]
        )
        fig.update_traces(
            line=dict(width=2),
            marker=dict(size=8)
        )
        fig.update_layout(
            hovermode="x unified",
            showlegend=False,
            yaxis=dict(tickformat=",", title=""),
            xaxis=dict(type="category", title="")
        )
        st.plotly_chart(fig, use_container_width=True, key=f"{table_type}_order_trend")

    with col2:
        if "revenue" in time_series.columns:
            fig = px.line(
                time_series,
                x="year_month",
                y="revenue",
                title="월별 매출",
                markers=True,
                labels={"year_month": "", "revenue": "매출"},
                color_discrete_sequence=[CHART_COLORS["revenue"]]
            )
            fig.update_traces(
                line=dict(width=2),
                marker=dict(size=8)
            )
            fig.update_layout(
                hovermode="x unified",
                showlegend=False,
                yaxis=dict(title="", tickformat=","),
                xaxis=dict(type="category", title="")
            )
            st.plotly_chart(fig, use_container_width=True, key=f"{table_type}_revenue_trend")
        else:
            st.info("revenue 컬럼이 없어 월별 매출 추이를 표시할 수 없습니다.")


# _render_distribution: 주요 컬럼 분포 차트 출력 내장 함수
def _render_distribution(distribution: dict, table_type: str = ""):
    """
    주요 카테고리 컬럼의 분포 차트를 출력합니다.

    Args:
        distribution (dict): 주요 컬럼 분포 정보
        table_type (str): 테이블 타입 (plotly_chart key 중복 방지용)

    Returns:
        없음

    Raises:
        없음
    """

    st.write("#### 주요 컬럼 분포")

    if not distribution:
        st.info("분포 분석 가능한 컬럼이 없습니다.")
        return

    color_map = {
        "order_status": CHART_COLORS["order"],
        "product_category": CHART_COLORS["category"],
        "payment_method": CHART_COLORS["revenue"]
    }

    cols = st.columns(len(distribution))

    for i, (col_name, dist_df) in enumerate(distribution.items()):
        with cols[i]:
            fig = px.bar(
                dist_df,
                x=col_name,
                y="count",
                title=col_name,
                labels={col_name: "", "count": "건"},
                color_discrete_sequence=[
                    color_map.get(col_name, CHART_COLORS["order"])
                ]
            )
            fig.update_layout(
                hovermode="closest",
                showlegend=False,
                yaxis=dict(title="", tickformat=","),
                xaxis=dict(title="")
            )
            st.plotly_chart(fig, use_container_width=True, key=f"{table_type}_{col_name}_dist")


# _render_column_stats: 수치형 / 문자열 컬럼 통계 출력 내장 함수
def _render_column_stats(numeric_stats: dict, categorical_stats: dict):
    """
    수치형 및 문자열 컬럼의 기초 통계를 출력합니다.

    Args:
        numeric_stats (dict): 수치형 컬럼 통계
        categorical_stats (dict): 문자열 컬럼 통계

    Returns:
        없음

    Raises:
        없음
    """

    st.write("#### 컬럼별 통계")

    tab1, tab2 = st.tabs(["수치형 컬럼", "문자열 컬럼"])

    with tab1:
        if numeric_stats:
            st.dataframe(
                pd.DataFrame(numeric_stats).T,
                use_container_width=True
            )
        else:
            st.info("수치형 컬럼이 없습니다.")

    with tab2:
        if categorical_stats:
            st.dataframe(
                pd.DataFrame(categorical_stats).T,
                use_container_width=True
            )
        else:
            st.info("문자열 컬럼이 없습니다.")