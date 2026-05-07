"""
upload_page.py

파일 업로드 화면 렌더링 모듈

기능:
    - Streamlit 파일 업로드 UI 생성
    - 업로드 파일 읽기 실행
    - 파일 메타데이터 출력
    - 데이터 미리보기 출력
"""


import streamlit as st

from python.app.services.file_uploader import (
    load_uploaded_file,
    create_file_metadata
)


# render_upload_page: 파일 업로드 화면을 렌더링하고 업로드 결과를 반환
def render_upload_page():
    """
    Streamlit 파일 업로드 화면을 렌더링

    Args:
        없음
    
    Returns:
        tuple:
            - pd.DataFrame | None: 업로드 파일을 읽어 생성한 DataFrame
            - dict | None: 업로드 파일의 메타데이터
    
    Raises:
        없음
    """

    # 페이지 제목
    st.title("All-in-One Commerce Analytics")

    # 현재 단계 표시
    st.subheader("1. 데이터 업로드")

    # 파일 업로드 UI
    uploaded_file = st.file_uploader(
        label="CSV 또는 Excel 파일을 업로드하세요.",
        type=["csv", "xlsx", "xls"]
    )

    # 파일이 아직 업로드되지 않은 경우
    if uploaded_file is None:
        st.info("분석할 이커머스 데이터를 업로드해주세요.")
        return None, None
    
    # 파일 읽기 및 메타데이터 생성
    try:
        df = load_uploaded_file(uploaded_file)
        metadata = create_file_metadata(uploaded_file, df)

        st.success("파일 업로드가 완료되었습니다.")

        # 파일 정보 출력
        st.write("### 파일 정보")
        st.write(f"파일명: {metadata['file_name']}")
        st.write(f"업로드 시간: {metadata['uploaded_at']}")
        st.write(f"행 개수: {metadata['row_count']}")
        st.write(f"컬럼 개수: {metadata['column_count']}")

        # 컬럼 목록 출력
        st.write("### 컬럼 목록")
        st.write(metadata["columns"])

        # 데이터 미리보기 출력
        st.write("### 데이터 미리보기")
        st.dataframe(df.head(20))

        return df, metadata
    
    except Exception as e:
        st.error(f"파일 업로드 중 오류가 발생했습니다: {e}")
        return None, None