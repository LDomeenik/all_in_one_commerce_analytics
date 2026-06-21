"""
preprocessing_page.py

전처리 UI 페이지 모듈

기능:
    - 전처리 실행 및 결과 출력
    - 전처리 요약 정보 출력
    - Flag 컬럼 기반 데이터 품질 리포트 출력
    - 전처리 완료 데이터 미리보기 출력
    - 전처리 결과 session_state 저장
"""


import streamlit as st

from core.analytics.table_selector import build_column_registry
from core.preprocessing.preprocessor import preprocess
from app.streamlit.session import (
    get_state,
    set_state,
    TABLES,
    PREPROCESSED_TABLES,
    CONFIRMED_MAPPING,
    PREPROCESSING_SUMMARY,
    COLUMN_REGISTRY
)


# render_preprocessing_page: 전처리 페이지 렌더링
def render_preprocessing_page():
    """
    전처리 페이지를 렌더링합니다.

    Args:
        없음

    Returns:
        없음

    Raises:
        없음
    """

    st.subheader("3단계. 전처리")

    # 매핑 완료 여부 확인
    tables = get_state(TABLES)

    if get_state(CONFIRMED_MAPPING) is None:
        st.warning("먼저 컬럼 매핑을 완료해주세요.")
        return

    # 전처리 실행 버튼
    if get_state(PREPROCESSED_TABLES) is None:
        st.write("매핑이 완료된 데이터에 전처리를 실행합니다.")
        st.write("타입 변환, 결측값 처리, 데이터 정합성 검증이 수행됩니다.")

        if st.button("전처리 실행", type="primary"):
            _run_preprocessing(tables)
    else:
        _render_preprocessing_result()


# _run_preprocessing: 전처리 실행
def _run_preprocessing(tables):
    """
    전처리를 실행하고 결과를 session_state 에 저장합니다.

    Args:
        tables (dict[str, pd.DataFrame]): 테이블 딕셔너리

    Returns:
        없음

    Raises:
        없음
    """

    with st.spinner("전처리 중..."):
        try:
            preprocessed_tables = {}
            combined_summary = {}

            for table_type, df in tables.items():
                # 각 테이블 전처리
                preprocessed_df, summary = preprocess(df)

                # 결과 저장
                preprocessed_tables[table_type] = preprocessed_df

                # summary 합산
                combined_summary["row_count"] = combined_summary.get("row_count", 0) + summary["row_count"]
                combined_summary["column_count"] = combined_summary.get("column_count", 0) + summary["column_count"]

                for flag, count in summary.get("flag_summary", {}).items():
                    combined_summary.setdefault("flag_summary", {})
                    combined_summary["flag_summary"][flag] = (
                        combined_summary["flag_summary"].get(flag, 0) + count
                    )
            
            set_state(PREPROCESSED_TABLES, preprocessed_tables)
            set_state(PREPROCESSING_SUMMARY, combined_summary)
            set_state(COLUMN_REGISTRY, build_column_registry(preprocessed_tables))

            st.rerun()

        except ValueError as e:
            st.error(f"전처리 중 오류가 발생했습니다: {e}")


# _render_preprocessing_result: 전처리 결과 출력
def _render_preprocessing_result():
    """
    전처리 결과 요약 및 데이터 미리보기를 출력합니다.

    Args:
        없음

    Returns:
        없음

    Raises:
        없음
    """

    preprocessed_tables = get_state(PREPROCESSED_TABLES)
    summary = get_state(PREPROCESSING_SUMMARY)

    st.success("전처리가 완료되었습니다.")

    # 요약 정보 출력
    st.write("#### 전처리 요약")
    col1, col2 = st.columns(2)

    with col1:
        st.metric("전체 행 수", f"{summary['row_count']:,}")
    with col2:
        st.metric("전체 컬럼 수", summary["column_count"])

    # 데이터 품질 리포트 출력
    flag_summary = summary.get("flag_summary", {})

    if flag_summary:
        st.write("#### 데이터 품질 리포트")
        st.warning(f"총 {len(flag_summary)}개 항목에서 오류가 발견되었습니다.")

        for flag, count in flag_summary.items():
            with st.expander(f"🔴 {flag} ({count}건)"):
                # 해당 Flag가 True인 행만 추출
                for table_type, df in preprocessed_tables.items():
                    if flag in df.columns:
                        error_rows = df[df[flag].eq(True)]

                        # Flag 컬럼 제외하고 표시
                        display_columns = [
                            col for col in error_rows.columns
                            if not col.startswith("is_")
                        ]
                        st.dataframe(
                            error_rows[display_columns],
                            use_container_width=True
                        )

    else:
        st.write("#### 데이터 품질 리포트")
        st.success("데이터 품질 오류가 발견되지 않았습니다.")

    # 전처리 완료 데이터 미리보기
    st.write("#### 전처리 완료 데이터 미리보기")

    # Flag 컬럼 제외하고 표시
    for table_type, df in preprocessed_tables.items():
        st.write(f"**{table_type} 테이블**")
        display_columns = [
            col for col in df.columns
            if not col.startswith("is_")
        ]
        st.dataframe(
            df[display_columns].head(20),
            use_container_width=True
        )

    # 재실행 버튼
    if st.button("전처리 재실행"):
        set_state(PREPROCESSED_TABLES, None)
        set_state(PREPROCESSING_SUMMARY, None)
        st.rerun()