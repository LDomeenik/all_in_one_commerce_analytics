"""
eda_page.py

EDA 분석 UI 페이지 모듈

기능:
    - EDA 분석 실행 및 결과 출력
    - 기초 통계 출력
    - 수치형 컬럼 통계 출력
    - 문자열 컬럼 통계 출력
    - 시계열 분포 차트 출력
    - 주요 컬럼 분포 차트 출력
"""


from re import M

import streamlit as st
import pandas as pd
import plotly.express as px

from core.analytics.eda import run_eda
from app.streamlit.session import (
    get_state,
    set_state,
    PREPROCESSED_DF,
    DIAGNOSIS_RESULT,
    EDA_RESULT
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

    # 전처리 완료 여부 확인
    preprocessed_df = get_state(PREPROCESSED_DF)

    if preprocessed_df is None:
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
        _run_eda(preprocessed_df)
    else:
        _render_eda_result()


# _run_eda: EDA 분석 실행 내장 함수
def _run_eda(preprocessed_df):
    """
    EDA 분석을 실행하고 결과를 session_state 에 저장합니다.

    Args:
        preprocessed_df (pd.DataFrame): 전처리 완료 DataFrame

    Returns:
        없음

    Raises:
        없음
    """

    # run_eda 실행 및 결과 저장
    with st.spinner("EDA 분석 중..."):
        try:
            eda_result = run_eda(preprocessed_df)
            set_state(EDA_RESULT, eda_result)
            st.rerun()

        except ValueError as e:
            st.error(f"EDA 분석 중 오류가 발생했습니다: {e}")


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

    # session_state 에서 EDA 결과 로드
    eda_result = get_state(EDA_RESULT)

    # 기초 통계 출력
    # _render_basic_stats 호출
    _render_basic_stats(eda_result["basic_stats"])
    st.divider()

    # 시계열 분포 차트 출력
    _render_time_series(eda_result["time_series"])
    st.divider()

    # 주요 컬럼 분포 차트 출력
    _render_distribution(eda_result["distribution"])
    st.divider()

    # 수치형 / 문자열 컬럼 통계 출력
    _render_column_stats(eda_result["numeric_stats"], eda_result["categorical_stats"])

    # 재실행 버튼
    if st.button("재실행"):
        set_state(EDA_RESULT, None)
        st.rerun()


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

    # 행 수, 컬럼 수, 분석 기간 메트릭 출력
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("전체 행 수", basic_stats["row_count"])
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


# _render_time_series: 시계열 분포 차트 출력 내장 함수
def _render_time_series(time_series: pd.DataFrame):
    """
    월별 주문 수 및 매출 추이 차트를 출력합니다.

    Args:
        time_series (pd.DataFrame): 시계열 집계 결과

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
            labels={"year_month":"", "order_count":"건"},
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
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if "revenue" in time_series.columns:
            fig = px.line(
                time_series,
                x="year_month",
                y="revenue",
                title="월별 매출",
                markers=True,
                labels={"year_month":"", "revenue":"매출"},
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
            st.plotly_chart(fig, use_container_width=True)


# _render_distribution: 주요 컬럼 분포 차트 출력 내장 함수
def _render_distribution(distribution: dict):
    """
    주요 카테고리 컬럼의 분포 차트를 출력합니다.

    Args:
        distribution (dict): 주요 컬럼 분포 정보

    Returns:
        없음

    Raises:
        없음
    """

    st.write("#### 주요 컬럼 분포")

    # distribution 이 비어있으면 안내 메시지 출력
    if not distribution:
        st.info("분포 분석 가능한 컬럼이 없습니다.")
        return

    # 컬럼별 색상 매핑
    color_map = {
        "order_status" : CHART_COLORS["order"],
        "product_category" : CHART_COLORS["category"],
        "payment_method" : CHART_COLORS["revenue"]
    }

    # 컬럼별 bar_chart 출력
    # 3열 그리드로 나란히 출력
    cols = st.columns(len(distribution))

    for i, (col_name, dist_df) in enumerate(distribution.items()):
        with cols[i]:
            fig = px.bar(
                dist_df,
                x=col_name,
                y="count",
                title=col_name,
                labels={col_name: "", "count": "건"},
                color_discrete_sequence=[color_map.get(col_name, CHART_COLORS["order"])]
            )
            fig.update_layout(
                hovermode="closest",
                showlegend=False,
                yaxis=dict(title="", tickformat=","),
                xaxis=dict(title="")
            )
            st.plotly_chart(fig, use_container_width=True)


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

    # 수치형 컬럼 통계 탭
    with tab1:
        if numeric_stats:
            st.dataframe(
                pd.DataFrame(numeric_stats).T,
                use_container_width=True
            )
        else:
            st.info("수치형 컬럼이 없습니다.")

    # 문자열 컬럼 통계 탭
    with tab2:
        if categorical_stats:
            st.dataframe(
                pd.DataFrame(categorical_stats).T,
                use_container_width=True
            )
        else:
            st.info("문자열 컬럼이 없습니다.")