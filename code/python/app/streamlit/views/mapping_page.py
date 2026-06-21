"""
mapping_page.py

컬럼 매핑 UI 페이지 모듈

기능:
    - 자동 매핑 실행 및 결과 출력
    - Confidence Score 기반 검수 상태 표시
    - 사용자 매핑 수정 UI 렌더링
    - 최종 매핑 확정 및 Staging DataFrame 생성
    - 매핑 결과 session_state 저장
"""


import pandas as pd
import streamlit as st

from core.mapping.mapper import map_columns, confirm_mapping, apply_mapping
from core.loader.config_loader import get_standard_column_list
from app.streamlit.session import (
    get_state,
    set_state,
    TABLES,
    MAPPING_RESULT,
    CONFIRMED_MAPPING,
    RENAME_DICT,
    UNMAPPED_COLUMNS
)


# _get_review_status: 검수 상태 반환 내장 함수
def _get_review_status(confidence: float, mapped_to) -> str:
    """
    Confidence Score와 매핑 여부를 기준으로 검수 상태를 반환합니다.

    Args:
        confidence (float): 매핑 신뢰도
        mapped_to (str | None): 매핑된 표준 컬럼명

    Returns:
        str: 검수 상태

    Raises:
        없음
    """

    if mapped_to is None:
        return "미매핑"
    if confidence >= 0.9:
        return "자동 매핑"
    if confidence >= 0.7:
        return "확인 필요"
    return "검수 필요"


# _build_mapping_df: 매핑 결과를 화면 출력용 DataFrame으로 변환하는 내장 함수
def _build_mapping_df(mapping_result: dict) -> pd.DataFrame:
    """
    매핑 결과 딕셔너리를 화면 출력용 DataFrame으로 변환합니다.

    Args:
        mapping_result (dict): 자동 매핑 결과

    Returns:
        pd.DataFrame: 화면 출력용 매핑 결과 DataFrame

    Raises:
        없음
    """

    rows = []

    for source_column, info in mapping_result.items():
        rows.append({
            "원본 컬럼명": source_column,
            "정규화된 컬럼명": info["normalized_column"],
            "매핑된 표준 컬럼": info["mapped_to"] if info["mapped_to"] else "-",
            "신뢰도": info["confidence"],
            "매핑 근거": ", ".join(info["source"]) if info["source"] else "-",
            "검수 상태": _get_review_status(info["confidence"], info["mapped_to"])
        })

    return pd.DataFrame(rows)


# render_mapping_page: 컬럼 매핑 페이지 렌더링
def render_mapping_page():
    """
    컬럼 매핑 페이지를 렌더링합니다.

    Args:
        없음

    Returns:
        없음

    Raises:
        없음
    """

    st.subheader("2단계. 컬럼 매핑")

    # 업로드된 파일 확인
    tables = get_state(TABLES)

    if not tables:
        st.warning("먼저 데이터를 업로드해주세요.")
        return

    # 테이블별 독립 매핑 실행
    if get_state(MAPPING_RESULT) is None:
        mapping_result = {}
        for table_type, df in tables.items():
            mapping_result[table_type] = map_columns(list(df.columns))
        set_state(MAPPING_RESULT, mapping_result)
    else:
        mapping_result = get_state(MAPPING_RESULT)

    # 매핑 결과 요약 출력
    _render_mapping_summary(mapping_result)

    st.divider()

    # 사용자 검수 UI
    _render_human_review(mapping_result)

    # 확정 완료 후 결과 표시
    if get_state(CONFIRMED_MAPPING) is not None:
        st.divider()
        _render_staging_preview()


# _render_mapping_summary: 매핑 결과 요약 출력 내장 함수
def _render_mapping_summary(mapping_result: dict):
    """
    매핑 결과 요약 정보를 출력합니다.

    Args:
        mapping_result (dict): 자동 매핑 결과

    Returns:
        없음

    Raises:
        없음
    """

    # 전체 집계
    all_rows = []
    for table_type, table_mapping in mapping_result.items():
        df = _build_mapping_df(table_mapping)
        df["테이블"] = table_type
        all_rows.append(df)

    mapping_df = pd.concat(all_rows, ignore_index=True)

    # 상태별 집계
    total = len(mapping_df)
    auto_mapped = len(mapping_df[mapping_df["검수 상태"] == "자동 매핑"])
    need_review = len(mapping_df[mapping_df["검수 상태"] == "확인 필요"])
    need_check = len(mapping_df[mapping_df["검수 상태"] == "검수 필요"])
    unmapped = len(mapping_df[mapping_df["검수 상태"] == "미매핑"])

    # 요약 메트릭 출력
    st.write("#### 자동 매핑 결과")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("전체 컬럼", total)
    with col2:
        st.metric("자동 매핑", auto_mapped)
    with col3:
        st.metric("확인 필요", need_review)
    with col4:
        st.metric("검수 필요", need_check)
    with col5:
        st.metric("미매핑", unmapped)

    # 매핑 결과 테이블 출력
    st.dataframe(mapping_df, use_container_width=True)


# _render_human_review: 사용자 검수 UI 렌더링 내장 함수
def _render_human_review(mapping_result: dict):
    """
    사용자가 매핑 결과를 수정하고 확정할 수 있는 UI를 렌더링합니다.

    Args:
        mapping_result (dict): 자동 매핑 결과

    Returns:
        없음

    Raises:
        없음
    """

    st.write("#### 최종 매핑 선택")
    st.write("자동 매핑 결과를 확인하고 잘못된 컬럼은 직접 수정해주세요.")

    # 표준 컬럼 목록 로드
    standard_column_list = get_standard_column_list()

    # 사용자 선택 결과 저장용 딕셔너리
    user_selections = {}

    for table_type, table_mapping in mapping_result.items():
        st.write(f"**{table_type} 테이블**")

        for source_column, info in table_mapping.items():
            mapped_to = info["mapped_to"]
            confidence = info["confidence"]
            status = _get_review_status(confidence, mapped_to)

            # 기본 선택값 설정
            if mapped_to in standard_column_list:
                default_index = standard_column_list.index(mapped_to)
            else:
                default_index = 0

            # 검수 상태에 따른 레이블 색상 표시
            if status == "미매핑":
                label = f"🔴 {source_column}"
            elif status == "검수 필요":
                label = f"🟡 {source_column}"
            elif status == "확인 필요":
                label = f"🟢 {source_column}"
            else:
                label = f"✅ {source_column}"

            selected = st.selectbox(
                label=label,
                options=standard_column_list,
                index=default_index,
                key=f"mapping_select_{table_type}_{source_column}"
            )

            user_selections[f"{table_type}_{source_column}"] = selected
    
        st.divider()

    # 최종 매핑 확정 버튼
    if st.button("최종 매핑 확정", type="primary"):
        _confirm_and_apply(mapping_result, user_selections)


# _confirm_and_apply: 매핑 확정 및 Staging DataFrame 생성 내장 함수
def _confirm_and_apply(mapping_result: dict, user_selections: dict):
    """
    사용자 확정 결과를 반영하고 Staging DataFrame을 생성합니다.

    Args:
        mapping_result (dict): 자동 매핑 결과
        user_selections (dict): 사용자가 선택한 매핑 결과

    Returns:
        없음

    Raises:
        없음
    """

    try:
        tables = get_state(TABLES)

        # 각 테이블에 매핑 적용
        mapped_tables = {}
        all_unmapped = []
        confirmed_mapping_all = {}

        for table_type, df in tables.items():
            table_mapping = mapping_result[table_type]

            # 이 테이블의 user_selections 추출
            table_selections = {
                col: user_selections[f"{table_type}_{col}"]
                for col in table_mapping.keys()
            }

            # 확정 매핑 생성
            confirmed = confirm_mapping(table_mapping, table_selections)
            confirmed_mapping_all[table_type] = confirmed

            # 매핑 적용
            mapped_df, rename_dict, unmapped_columns = apply_mapping(df, confirmed)
            mapped_tables[table_type] = mapped_df
            all_unmapped.extend(unmapped_columns)

        set_state(CONFIRMED_MAPPING, confirmed_mapping_all)
        set_state(TABLES, mapped_tables)
        set_state(RENAME_DICT, rename_dict)
        set_state(UNMAPPED_COLUMNS, all_unmapped)

        # 강제 재실행으로 사이드바 상태 즉시 업데이트
        st.rerun()

    except ValueError as e:
        st.error(f"매핑 적용 중 오류가 발생했습니다: {e}")
        st.info("💡 같은 표준 컬럼으로 매핑된 원본 컬럼이 있습니다. 위 매핑 선택에서 하나를 'None'으로 변경해주세요.")


# _render_staging_preview: Staging 데이터 미리보기 출력 내장 함수
def _render_staging_preview():
    """
    확정된 매핑 결과와 Staging DataFrame 미리보기를 출력합니다.

    Args:
        없음

    Returns:
        없음

    Raises:
        없음
    """

    tables = get_state(TABLES)
    unmapped_columns = get_state(UNMAPPED_COLUMNS)

    st.subheader("3단계 준비 완료")
    st.success("최종 매핑이 확정되었습니다.")

    # 미매핑 컬럼 경고
    if unmapped_columns:
        st.warning(
            f"미매핑 컬럼 {len(unmapped_columns)}개가 "
            f"Staging에서 제외됩니다: {unmapped_columns}"
        )

    # 각 테이블별 미리보기 출력
    st.write("#### Staging 데이터 미리보기")
    for table_type, df in tables.items():
        st.write(f"**{table_type} 테이블**")
        st.dataframe(df.head(20), use_container_width=True)