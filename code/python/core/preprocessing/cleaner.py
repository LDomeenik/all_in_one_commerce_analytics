"""
cleaner.py

Staging DataFrame의 문자열 정규화 및 결측값 처리 모듈

기능:
    - 문자열로 표현된 결측값을 pd.NA로 정규화
    - 문자열 컬럼 앞뒤 공백 제거
"""


import pandas as pd


# 결측값으로 처리할 문자열 목록
MISSING_STRING_VALUES = {
    "", " ", "na", "n/a", "null", "none", "nan", "-"
}


# normalize_missing_values: 문자열 결측값을 pd.NA로 정규화
def normalize_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    문자열로 표현된 결측값을 pd.NA로 정규화합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame
    
    Returns:
        pd.DataFrame: 결측값이 정규화된 DataFrame
    
    Raises:
        없음
    """

    # 원본 보존용 복사본 생성
    result_df = df.copy()

    for column in result_df.columns:
        if pd.api.types.is_string_dtype(result_df[column]):
            result_df[column] = result_df[column].apply(
                lambda value: 
                pd.NA if isinstance(value, str) and value.strip().lower() in MISSING_STRING_VALUES else value
            )
    
    return result_df


# strip_string_columns: 문자열 컬럼 앞뒤 공백 제거
def strip_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    문자열 컬럼의 앞뒤 공백을 제거합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame
    
    Returns:
        pd.DataFrame: 공백이 제거된 DataFrame
    
    Raises:
        없음
    """

    # 원본 보존용 복사본 생성
    result_df = df.copy()

    for column in result_df.columns:
        if pd.api.types.is_string_dtype(result_df[column]):
            result_df[column] = result_df[column].apply(
                lambda value:
                value.strip() if isinstance(value, str) else value
            )
    
    return result_df


# clean_dataframe: 전체 정제 실행
def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Staging DataFrame에 전체 정제 과정을 적용합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame
    
    Returns:
        pd.DataFrame: 정제된 DataFrame
    
    Raises:
        없음
    """

    # 문자열 앞뒤 공백 제거 후 결측값 정규화
    result_df = strip_string_columns(df)
    result_df = normalize_missing_values(result_df)

    return result_df