"""
mapping_result_view.py

컬럼 매핑 결과 화면 출력 모듈

기능:
    - 컬럼 매핑 결과를 DataFrame으로 변환
    - 미매핑 컬럼 개수 계산
    - Streamlit 화면에 컬럼 매핑 결과 출력
"""


import pandas as pd
import streamlit as st


# convert_mapping_result_to_dataframe: 컬럼 매핑 결과를 화면 출력용 DataFrame으로 변환
def convert_mapping_result_to_dataframe(mapping_result: dict) -> pd.DataFrame:
    """
    컬럼 매핑 결과 딕셔너리를 Streamlit 출력용 DataFrame으로 변환

    Args:
        mapping_result (dict): 원본 컬럼별 컬럼 매핑 결과
    
    Returns:
        pd.DataFrame: 컬럼 매핑 결과 DataFrame
    
    Raises:
        없음
    """

    # 딕셔너리를 DtaFrame으로 변환
    mapping_df = pd.DataFrame.from_dict(
        mapping_result,
        orient="index"
    )

    # index를 일반 컬럼으로 변환
    mapping_df = mapping_df.reset_index()

    # 컬럼명 변경
    mapping_df = mapping_df.rename(
        columns={
            "index" : "source_column"
        }
    )

    return mapping_df


# count_unmapped_columns: 미매핑 컬럼 개수 계산
def count_unmapped_columns(mapping_df: pd.DataFrame) -> int:
    """
    컬럼 매핑 결과에서 미매핑 컬럼 개수를 계산

    Args:
        mapping_df (pd.DataFrmae): 컬럼 매핑 결과 DataFrame
    
    Returns:
        int: 미매핑 컬럼 개수
    
    Raises:
        없음
    """

    # mapped_to가 비어 있는 컬럼 수 계산
    unmapped_count = mapping_df["mapped_to"].isna().sum()

    return unmapped_count


# render_mapping_result: 컬럼 매핑 결과를 Streamlit 화면에 출력
def render_mapping_result(mapping_result: dict):
    """
    컬럼 매핑 결과를 Streamlit 화면에 출력

    Args:
        mapping_result (dict): 원본 컬럼별 컬럼 매핑 결과
    
    Returns:
        pd.DataFrame: 컬럼 매핑 결과 DataFrame
    
    Raises:
        없음
    """

    # mapping 데이터프레임 지정
    mapping_df = convert_mapping_result_to_dataframe(mapping_result)

    # mapping되지 않은 컬럼 개수 지정
    unmapped_count = count_unmapped_columns(mapping_df)

    st.write("### 컬럼 자동 매핑 결과")
    st.dataframe(mapping_df)

    if unmapped_count == 0:
        st.success("모든 컬럼이 Alias Dictionary 기준으로 매핑되었습니다.")
    else:
        st.warning(f"미매핑 컬럼이 {unmapped_count}개 있습니다.")
    
    return mapping_df