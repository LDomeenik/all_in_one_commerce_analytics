"""
type_converter.py

Staging DataFrame의 컬럼 타입을 표준 타입으로 변환하는 모듈

기능:
    - standard_columns.json 기준 타입 정보 로드
    - 날짜 컬럼 datetime 변환 및 변환 실패 Flag 생성
    - 숫자 컬럼 numeric 변환 및 변환 실패 Flag 생성
    - 정수 컬럼 integer 변환 및 변환 실패 Flag 생성
    - 불리언 컬럼 boolean 변환 및 변환 실패 Flag 생성
    - 전체 타입 변환 실행
"""


import pandas as pd

from core.loader.config_loader import get_columns_by_type


# 불리언 변환 매핑 테이블
BOOLEAN_TRUE_VALUES = {"true", "1", "yes", "y"}
BOOLEAN_FALSE_VALUES = {"false", "0", "no", "n"}


# _to_boolean: 단일 값을 boolean으로 변환하는 내장 함수
def _to_boolean(value):
    """
    단일 값을 boolean으로 변환합니다.

    Args:
        value: 변환할 값
    
    Returns:
        bool | pd.NA: 변환된 boolean 값 또는 변환 실패 시 pd.NA
    
    Raises:
        없음
    """
    
    if pd.isna(value):
        return pd.NA
    str_value = str(value).strip().lower()
    if str_value in BOOLEAN_TRUE_VALUES:
        return True
    if str_value in BOOLEAN_FALSE_VALUES:
        return False
    return pd.NA


# _convert_date_columns: 날짜 컬럼 변환
def _convert_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    날짜 타입 표준 컬럼을 datetime으로 변환합니다. 변환 실패 시 is_invalid_{column} Flag를 생성합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame
    
    Returns:
        pd.DataFrame: 날짜 컬럼이 변환된 DataFrame
    
    Raises:
        없음
    """

    result_df = df.copy()
    date_columns = get_columns_by_type("date")

    for column in date_columns:
        if column not in result_df.columns:
            continue

        original_not_null = result_df[column].notna()

        result_df[column] = pd.to_datetime(
            result_df[column],
            errors="coerce"
        )

        # 변환 실패 Flag 생성
        result_df[f"is_invalid_{column}"] = (
            original_not_null & result_df[column].isna()
        )

    return result_df


# _convert_numeric_columns: 숫자 컬럼 변환
def _convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    숫자 타입 표준 컬럼을 numeric으로 변환합니다. 쉼표 및 통화기호 제거 후 변환합니다. 변환 실패 시 is_invalid_{column} Flag를 생성합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame
    
    Returns:
        pd.DataFrame: 숫자 컬럼이 변환된 DataFrame
    
    Raises:
        없음
    """

    result_df = df.copy()
    numeric_columns = get_columns_by_type("numeric")

    for column in numeric_columns:
        if column not in result_df.columns:
            continue

        original_not_null = result_df[column].notna()

        # 문자열인 경우 쉼표 및 통화기호 제거
        if pd.api.types.is_string_dtype(result_df[column]):
            result_df[column] = (
                result_df[column]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("₩", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.replace("€", "", regex=False)
                .str.strip()
            )

        result_df[column] = pd.to_numeric(
            result_df[column],
            errors="coerce"
        )

        result_df[f"is_invalid_{column}"] = (
            original_not_null & result_df[column].isna()
        )
    
    return result_df


# _convert_integer_columns: 정수 컬럼 변환
def _convert_integer_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    정수 타입 표준 컬럼을 integer로 변환합니다. 변환 실패 시 is_invalid_{column} Flag를 생성합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame
    
    Returns:
        pd.DataFrame: 정수 컬럼이 변환된 DataFrame
    
    Raises:
        없음
    """

    result_df = df.copy()
    integer_columns = get_columns_by_type("integer")

    for column in integer_columns:
        if column not in result_df.columns:
            continue

        original_not_null = result_df[column].notna()

        result_df[column] = pd.to_numeric(
            result_df[column],
            errors="coerce"
        )

        # 변환 실패 Flag 생성
        result_df[f"is_invalid_{column}"] = (
            original_not_null & result_df[column].isna()
        )
    
    return result_df


# _convert_boolean_columns: 불리언 컬럼 변환
def _convert_boolean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    불리언 타입 표준 컬럼을 boolean으로 변환합니다. 변환 실패 시 is_invalid_{column} Flag를 생성합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame
    
    Returns:
        pd.DataFrame: 불리언 컬럼이 변환된 DataFrame
    
    Raises:
        없음
    """

    result_df = df.copy()
    boolean_columns = get_columns_by_type("boolean")

    for column in boolean_columns:
        if column not in result_df.columns:
            continue

        original_not_null = result_df[column].notna()
        
        result_df[column] = result_df[column].apply(_to_boolean)

        # 변환 실패 Flag 생성
        result_df[f"is_invalid_{column}"] = (
            original_not_null & result_df[column].isna()
        )
    
    return result_df


# convert_column_types: 전체 타입 변환 실행
def convert_column_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Staging DataFrame의 전체 컬럼 타입 변환을 실행합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame
    
    Returns:
        pd.DataFrame: 타입 변환이 완료된 DataFrame
    
    Raises:
        없음
    """

    result_df = _convert_date_columns(df)
    result_df = _convert_numeric_columns(result_df)
    result_df = _convert_integer_columns(result_df)
    result_df = _convert_boolean_columns(result_df)

    return result_df