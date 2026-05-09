"""
upload_page.py

파일 업로드 화면 렌더링 모듈

기능:
    - Streamlit 파일 업로드 UI 생성
    - 업로드 파일 읽기 실행
    - 파일 메타데이터 출력
    - 데이터 미리보기 출력
    - 컬럼 자동 매핑 화면 출력
"""


import streamlit as st

from python.app.services.file_uploader import (
    load_uploaded_file,
    create_file_metadata
)

from python.app.services.column_mapper import map_columns
from python.app.services.column_mapping_applier import apply_column_mapping

from python.app.ui.mapping_result_view import render_mapping_result



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
        return None, None, None
    
    # 파일 읽기 및 메타데이터 생성
    try:
        raw_df = load_uploaded_file(uploaded_file)
        metadata = create_file_metadata(uploaded_file, raw_df)

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
        st.dataframe(raw_df.head(20))

        # 컬럼 자동 매핑 실행
        mapping_result = map_columns(metadata["columns"])

        # 컬럼 자동 매핑 결과 출력
        confirmed_mapping_result = render_mapping_result(mapping_result)
        
        if confirmed_mapping_result is not None:
            st.session_state["confirmed_mapping_result"] = confirmed_mapping_result

            # staging_df 생성
            staging_df, rename_dict, unmapped_columns = apply_column_mapping(
                df=raw_df,
                confirmed_mapping_result=confirmed_mapping_result
            )

            st.session_state["staging_df"] = staging_df
            st.session_state["rename_dict"] = rename_dict
            st.session_state["unmapped_columns"] = unmapped_columns

            st.divider()
            st.subheader("3. 표준 컬럼 적용 결과")
            
            st.write("### 적용된 컬럼 매핑")
            st.json(rename_dict)

            if len(unmapped_columns) > 0:
                st.warning(f"Staging에서 제외될 미매핑 컬럼: {unmapped_columns}")
            else:
                st.success("미매핑 컬럼 없이 모든 컬럼이 Staging에 반영됩니다.")
            
            st.write("### Staging 데이터 미리보기")
            st.dataframe(staging_df.head(20))

        return raw_df, metadata, confirmed_mapping_result
    
    except Exception as e:
        st.error(f"파일 업로드 중 오류가 발생했습니다: {e}")
        return None, None, None