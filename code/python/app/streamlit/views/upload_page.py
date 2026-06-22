"""
upload_page.py

파일 업로드 UI 페이지 모듈

기능:
    - 단일 / 다중 파일 업로드 UI 렌더링
    - 단일 파일: 자동으로 order 테이블로 분류
    - 다중 파일: 테이블 유형 자동 추론 후 사용자 확인/수정
    - 분류 결과를 TABLES로 저장
"""


import streamlit as st

from core.loader.file_reader import read_file, read_multiple_files, create_file_metadata
from core.loader.table_classifier import infer_table_type, TABLE_RULES
from app.streamlit.session import (
    set_state, get_state,
    UPLOADED_FILES, FILE_METADATA,
    TABLES, TABLE_TYPES
)


# render_upload_page: 파일 업로드 페이지 렌더링
def render_upload_page():
    """
    파일 업로드 페이지를 렌더링합니다.
    단일 파일이면 바로 TABLES로 저장하고,
    다중 파일이면 테이블 유형 확인/수정 UI를 렌더링합니다.

    Args:
        없음

    Returns:
        없음

    Raises:
        없음
    """

    st.subheader("1단계. 데이터 업로드")
    st.write("분석할 이커머스 데이터를 업로드해주세요.")

    # 단일/다중 파일 모두 지원하는 업로드 UI
    uploaded_files = st.file_uploader(
        label="CSV 또는 Excel 파일을 업로드하세요.",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True
    )

    # 파일이 업로드되지 않은 경우
    if not uploaded_files:
        # 이전에 업로드된 파일이 있으면 미리보기 유지
        if get_state(TABLES) is not None:
            _render_tables_preview()
        return

    # 단일 파일이면 바로 order로 저장
    if len(uploaded_files) == 1:
        _render_single_upload(uploaded_files[0])
    # 다중 파일이면 테이블 유형 확인/수정 UI 렌더링
    elif len(uploaded_files) >= 2:
        _render_multi_upload(uploaded_files)

    # 업로드 완료 후 미리보기 출력
    _render_tables_preview()


# _render_single_upload: 단일 파일 처리
def _render_single_upload(uploaded_file):
    """
    단일 파일을 읽어 TABLES = {"order": df}로 저장합니다.

    Args:
        uploaded_file: 업로드된 파일 객체

    Returns:
        없음

    Raises:
        없음
    """

    try:
        # 파일 읽기 및 메타데이터 생성
        raw_df = read_file(uploaded_file)
        metadata = create_file_metadata(uploaded_file, raw_df)

        # 단일 파일은 order 테이블로 저장
        set_state(TABLES, {"order": raw_df})
        set_state(FILE_METADATA, metadata)

        st.success("파일 업로드가 완료되었습니다.")

    except ValueError as e:
        st.error(f"파일 업로드 중 오류가 발생했습니다: {e}")


# _render_multi_upload: 다중 파일 처리
def _render_multi_upload(uploaded_files: list):
    """
    여러 파일을 읽어 테이블 유형을 자동 추론하고
    사용자 확인/수정 UI를 렌더링합니다.

    Args:
        uploaded_files (list): 업로드된 파일 객체 리스트

    Returns:
        없음

    Raises:
        없음
    """

    try:
        # 여러 파일 읽기
        files_dict = read_multiple_files(uploaded_files)

        # UPLOADED_FILES 저장
        set_state(UPLOADED_FILES, files_dict)

        # 테이블 유형 확인/수정 UI 렌더링
        _render_table_type_selector(files_dict)

    except ValueError as e:
        st.error(f"파일 업로드 중 오류가 발생했습니다: {e}")


# _render_table_type_selector: 테이블 유형 확인/수정 UI
def _render_table_type_selector(files_dict: dict):
    """
    각 파일의 테이블 유형을 확인하고 수정할 수 있는 UI를 렌더링합니다.
    확정 버튼 클릭 시 TABLES로 저장합니다.

    Args:
        files_dict (dict): {파일명: DataFrame}

    Returns:
        없음

    Raises:
        없음
    """

    st.write("#### 테이블 유형 확인")
    st.write("자동으로 추론된 테이블 유형을 확인하고 수정해주세요.")

    # selectbox 선택지 (TABLE_RULES 키 + unknown)
    options = list(TABLE_RULES.keys()) + ["unknown"]

    # 파일별 사용자 선택값 저장
    selected_types = {}

    # 각 파일마다 테이블 유형 추론 + selectbox 렌더링
    for file_name, df in files_dict.items():
        # 자동 추론
        inferred = infer_table_type(df)

        # 추론된 유형의 인덱스 계산 (기본 선택값)
        default_index = options.index(inferred) if inferred in options else 0

        # selectbox로 사용자 확인/수정
        selected = st.selectbox(
            label=file_name,
            options=options,
            index=default_index
        )

        # 사용자 선택값 저장
        selected_types[file_name] = selected

    # 확정 버튼 클릭 시 TABLES 저장
    if st.button("확정"):
        tables = {}
        for file_name, table_type in selected_types.items():
            tables[table_type] = files_dict[file_name]

        set_state(TABLES, tables)
        set_state(TABLE_TYPES, selected_types)

        st.success("테이블 유형이 확정되었습니다.")


# _get_ordered_table_types: 테이블 탭 출력 순서 반환
def _get_ordered_table_types(data: dict) -> list:
    """
    테이블 타입을 지정된 우선순위에 따라 정렬합니다.

    우선순위:
        1. order
        2. order_item
        3. customer
        4. 그 외 추가 테이블

    Args:
        data (dict): 테이블 타입을 key로 가지는 딕셔너리

    Returns:
        list: 정렬된 테이블 타입 리스트

    Raises:
        없음
    """

    priority = ["order", "order_item", "customer"]

    ordered = [
        table_type
        for table_type in priority
        if table_type in data
    ]

    others = [
        table_type
        for table_type in data.keys()
        if table_type not in priority
    ]

    return ordered + others


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
        "order": "📦",
        "order_item": "🧾",
        "customer": "👥",
        "product": "🛍️",
        "payment": "💳",
        "delivery": "🚚"
    }

    return icon_map.get(table_type, "📄")


# _get_table_label: 테이블 타입별 표시명 반환
def _get_table_label(table_type: str) -> str:
    """
    테이블 타입에 맞는 사용자 표시명을 반환합니다.

    Args:
        table_type (str): 테이블 타입

    Returns:
        str: 사용자 표시명

    Raises:
        없음
    """

    label_map = {
        "order": "주문",
        "order_item": "주문 상품",
        "customer": "고객",
        "product": "상품",
        "payment": "결제",
        "delivery": "배송"
    }

    return label_map.get(table_type, table_type)


# _render_tables_preview: 분류 결과 미리보기
def _render_tables_preview():
    """
    TABLES에 저장된 테이블 분류 결과를 미리보기로 출력합니다.

    Args:
        없음

    Returns:
        없음

    Raises:
        없음
    """

    # TABLES 가져오기
    tables = get_state(TABLES)

    # TABLES가 없으면 반환
    if not tables:
        return

    st.write("#### 업로드 데이터 미리보기")

    # 테이블별 탭 순서 정렬
    table_types = _get_ordered_table_types(tables)

    tab_labels = [
        f"{_get_table_icon(table_type)} {_get_table_label(table_type)}"
        for table_type in table_types
    ]

    tabs = st.tabs(tab_labels)

    for tab, table_type in zip(tabs, table_types):
        with tab:
            df = tables[table_type]

            st.write(f"### {_get_table_label(table_type)} 테이블")
            st.caption(f"내부 테이블 타입: `{table_type}`")

            # 행/컬럼 수 출력
            col1, col2 = st.columns(2)

            with col1:
                st.metric("행 수", f"{len(df):,}")

            with col2:
                st.metric("컬럼 수", len(df.columns))

            # 컬럼 목록 간단 표시
            with st.expander("컬럼 목록 보기"):
                st.write(list(df.columns))

            # 데이터 미리보기 출력
            st.dataframe(
                df.head(5),
                use_container_width=True
            )