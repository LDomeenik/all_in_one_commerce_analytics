"""
preprocessor.py

Staging DataFrame 전체 전처리 과정을 통합 실행하는 모듈

기능:
    - 문자열 정규화 및 결측값 처리 실행
    - 컬럼 타입 변환 실행
    - 데이터 정합성 검증 및 Flag 생성 실행
    - 전처리 결과 요약 정보 생성
    - 전체 전처리 통합 실행
"""


import pandas as pd

from core.preprocessing.cleaner import clean_dataframe
from core.preprocessing.type_converter import convert_column_types
from core.preprocessing.validator import validate_dataframe


# _create_preprocessing_summary: 전처리 결과 요약 정보 생성
def _create_preprocessing_summary(df: pd.DataFrame) -> dict:
    """
    전처리 완료 DataFrame 의 요약 정보를 생성합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame

    Returns:
        dict: 전처리 결과 요약 정보
            - row_count (int): 전체 행 수
            - column_count (int): 전체 컬럼 수
            - flag_summary (dict): Flag 컬럼별 True 개수

    Raises:
        없음
    """

    # Flag 컬럼 목록 추출
    flag_columns = [
        column for column in df.columns
        if column.startswith("is_")
    ]

    # Flag 컬럼별 True 개수 계산
    flag_summary = {}

    for column in flag_columns:
        true_count = int(df[column].sum())
        if true_count > 0:
            flag_summary[column] = true_count

    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "flag_summary": flag_summary
    }


# preprocess: 전체 전처리 통합 실행
def preprocess(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Staging DataFrame 에 전체 전처리 과정을 실행합니다.

    Args:
        df (pd.DataFrame): 컬럼 매핑이 완료된 Staging DataFrame

    Returns:
        tuple:
            - pd.DataFrame: 전처리 완료 DataFrame
            - dict: 전처리 결과 요약 정보

    Raises:
        ValueError: 입력 DataFrame 이 비어 있는 경우
    """

    if df is None or df.empty:
        raise ValueError("전처리할 데이터가 없습니다.")

    # 1. 문자열 정규화 및 결측값 처리
    result_df = clean_dataframe(df)

    # 2. 컬럼 타입 변환
    result_df = convert_column_types(result_df)

    # 3. 데이터 정합성 검증 및 Flag 생성
    result_df = validate_dataframe(result_df)

    # 4. 전처리 결과 요약 생성
    summary = _create_preprocessing_summary(result_df)

    return result_df, summary