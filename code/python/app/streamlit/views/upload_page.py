"""
upload_page.py

파일 업로드 UI 페이지 모듈

기능:
    - 파일 업로드 UI 렌더링
    - 업로드 파일 읽기 및 메타데이터 생성
    - 파일 정보 및 데이터 미리보기 출력
    - 업로드 결과 session_state 저장
"""


import streamlit as st

from core.loader.file_reader import read_file, create_file_metadata
from app.streamlit.session import set_state, get_state, RAW_DF, FILE_METADATA


# render_upload_page: 파일 업로드 페이지 렌더링
def render_upload_page():
    """
    파일 업로드 페이지를 렌더링합니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    st.subheader("1단계. 데이터 업로드")
    st.write("분석할 이커머스 데이터를 업로드해주세요.")

    # 파일 업로드 UI
    uploaded_file = st.file_uploader(
        label="CSV 또는 Excel 파일을 업로드하세요.",
        type=["csv", "xlsx", "xls"]
    )

    # 파일이 업로드되지 않은 경우
    if uploaded_file is None:
        # 이전에 업로드된 파일이 있으면 유지
        if get_state(RAW_DF) is not None:
            _render_file_info()
        return
    
    try:
        raw_df = read_file(uploaded_file)
        metadata = create_file_metadata(uploaded_file, raw_df)
        
        set_state(RAW_DF, raw_df)
        set_state(FILE_METADATA, metadata)

        _render_file_info()
    
    except ValueError as e:
        st.error(f"파일 업로드 중 오류가 발생했습니다: {e}")


# _render_file_info: 파일 정보 및 데이터 미리보기 출력하는 내장함수
def _render_file_info():
    """
    저장된 파일 정보와 데이터 미리보기를 출력합니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    metadata = get_state(FILE_METADATA)
    raw_df = get_state(RAW_DF)

    if metadata is None or raw_df is None:
        return
    
    # 파일 정보 출력
    st.success("파일 업로드가 완료되었습니다.")

    st.write("#### 파일 정보")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("파일명", metadata["file_name"])
    with col2:
        st.metric("행 개수", f"{metadata['row_count']:,}")
    with col3:
        st.metric("컬럼 개수", metadata["column_count"])
    
    # 컬럼 목록 출력
    st.write("#### 컬럼 목록")
    st.write(metadata["columns"])

    # 데이터 미리보기 출력
    st.write("#### 데이터 미리보기")
    st.dataframe(raw_df.head(20))