"""
preprocessor.py

Staging DataFrame 전처리 모듈

기능:
    - 문자열 결측값 정규화
    - 문자열 컬럼 공백 제거
    - 날짜 컬럼 타입 변환
    - 숫자 컬럼 타입 변환
    - 필수 컬럼 결측 여부 Flag 생성
    - 기본 데이터 정합성 Flag 생성
    - 전처리 요약 정보 생성
"""


import pandas as pd


# 필수 컬럼 정의
REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "customer_id",
    "revenue"
]

# 날짜 컬럼 정의
DATE_COLUMNS = [
    "order_date",
    "shipped_date",
    "delivered_date"
]

# 숫자형 컬럼 정의
NUMERIC_COLUMNS = [
    "revenue",
    "quantity",
    "unit_price",
    "shipping_fee",
    "discount_amount",
    "review_score",
    "review_count"
]

# 결측값 정의
MISSING_VALUES = [
    "",
    " ",
    "na",
    "n/a",
    "null",
    "none",
    "nan",
    "-"
]


# normalize_missing_values: 문자열 결측 표현을 pandas 결측값으로 변환
def normalize_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    문자열로 표현된 결측값을 pd.NA로 변환

    Args:
        df (pd.DataFrame): Staging DataFrame
    
    Returns:
        pd.DataFrame: 결측값이 표준화된 DataFrame
    
    Raises:
        없음
    """

    # 원본 보존을 위한 복사본 생성
    result_df = df.copy()

    # 문자열 타입 컬럼 결측값 처리
    for column in result_df.columns:
        if result_df[column].dtype == "object":
            result_df[column] = result_df[column].apply(
                lambda value: 
                    pd.NA if isinstance(value, str) and value.strip().lower() in MISSING_VALUES else value
            )
    
    return result_df


# strip_string_columns: 문자열 컬럼의 앞뒤 공백 제거
def strip_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    문자열 컬럼의 앞뒤 공백을 제거

    Args:
        df (pd.DataFrame): Staging DataFrame
    
    Returns:
        pd.DataFrame: 문자열 공백이 정리된 DataFrame
    
    Raises:
        없음
    """

    # 원본 보존용 복사본 생성
    result_df = df.copy()

    # 문자열 타입 컬럼 앞뒤 공백 제거
    for column in result_df.columns:
        if result_df[column].dtype == "object":
            result_df[column] = result_df[column].apply(
                lambda value:
                    value.strip() if isinstance(value, str) else value
            )
    
    return result_df


# convert_date_columns: 날짜 컬럼을 datetime 타입으로 변환
def convert_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    날짜 컬럼을 datetime 타입으로 변환하고 변환 실패 여부 Flag를 생성

    Args:
        df (pd.DataFrame): Staging DataFrame

    Returns:
        pd.DataFrame: 날짜 컬럼이 변환된 DataFrame
    
    Raises:
        없음
    """

    # 원본 보존용 복사본 생성
    result_df = df.copy()

    # 날짜 컬럼 타입 변환
    for column in DATE_COLUMNS:
        if column in result_df.columns:
            original_not_null = result_df[column].notna()

            result_df[column] = pd.to_datetime(
                result_df[column],
                errors="coerce"
            )

            # 날짜 변환 실패 여부 Flag 생성
            result_df[f"is_invalid_{column}"] = (
                original_not_null & result_df[column].isna()
            )
    
    return result_df


# convert_numeric_columns: 숫자 컬럼을 numeric 타입으로 변환
def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    숫자 컬럼을 numeric 타입으로 변환하고 변환 실패 여부 Flag를 생성

    Args:
        df (pd.DataFrame): Staging DataFrame
    
    Returns:
        pd.DataFrame: 숫자 컬럼이 변환된 DataFrame
    
    Raises:
        없음
    """

    # 원본 보존용 복사본 생성
    result_df = df.copy()

    # 숫자 컬럼 타입 변환
    for column in NUMERIC_COLUMNS:
        if column in result_df.columns:
            original_not_null = result_df[column].notna()

            if result_df[column].dtype == "object":
                result_df[column] = (
                    result_df[column]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                    .str.replace("₩", "", regex=False)
                    .str.replace("$", "", regex=False)
                    .str.strip()
                )
        
            result_df[column] = pd.to_numeric(
                result_df[column],
                errors="coerce"
            )

            # 변환 실패 여부 Flag 생성
            result_df[f"is_invalid_{column}"] = (
                original_not_null & result_df[column].isna()
            )
    
    return result_df


# add_missing_flags: 필수 컬럼 결측 여부 Flag 생성
def add_missing_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    필수 컬럼의 결측 여부 Flag를 생성

    Args:
        df (pd.DataFrame): Staging DataFrame
    
    Returns:
        pd.DataFrame: 필수 컬럼 결측 Flag가 추가된 DataFrame
    
    Raises:
        없음
    """

    # 원본 보존용 복사본 생성
    result_df = df.copy()

    # 필수 컬럼 결측 상태 기록
    for column in REQUIRED_COLUMNS:
        if column in result_df.columns:
            result_df[f"is_missing_{column}"] = result_df[column].isna()
        
        else:
            result_df[f"is_missing_{column}"] = True
    
    return result_df


# add_consistency_flags: 기본 데이터 정합성 Flag 생성
def add_consistency_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    기본 데이터 정합성 검증 Falg를 생성

    Args:
        df (pd.DataFrame): Staging DataFrame
    
    Returns:
        pd.DataFrame: 정합성 검증 Flag가 추가된 DataFrame
    
    Raises:
        없음
    """

    # 원본 보존용 복사본 생성
    result_df = df.copy()

    # revenue 음수 여부 검증
    if "revenue" in result_df.columns:
        result_df["is_negative_revenue"] = (
            result_df["revenue"] < 0
        )
    
    # quantity 0 이하 여부 검증
    if "quantity" in result_df.columns:
        result_df["is_invalid_quantity"] = (
            result_df["quantity"] <= 0
        )
    
    # unit_price 음수 여부 검증
    if "unit_price" in result_df.columns:
        result_df["is_negative_unit_price"] = (
            result_df["unit_price"] < 0
        )
    
    # shipping_fee 음수 여부 검증
    if "shipping_fee" in result_df.columns:
        result_df["is_negative_shipping_fee"] = (
            result_df["shipping_fee"] < 0
        )
    
    # 주문일 > 배송완료일 여부 검증
    if (
        "order_date" in result_df.columns
        and "delivered_date" in result_df.columns
    ):
        result_df["is_invalid_delivery_flow"] = (
            result_df["order_date"].notna() & result_df["delivered_date"].notna()
            & (result_df["order_date"] > result_df["delivered_date"])
        )
    
    # 주문일 > 출고일 여부 검증
    if (
        "order_date" in result_df.columns
        and "shipped_date" in result_df.columns
    ):
        result_df["is_invalid_shipping_flow"] = (
            result_df["order_date"].notna() & result_df["shipped_date"].notna()
            & (result_df["order_date"] > result_df["shipped_date"])
        )
    
    return result_df


# create_preprocessing_summary: 전처리 요약 정보 생성
def create_preprocessing_summary(df: pd.DataFrame) -> dict:
    """
    전처리 결과 요약 정보를 생성

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
    
    Returns:
        dict: 전처리 결과 요약 정보
    
    Raises:
        없음
    """

    # Flag 컬럼 목록 추출
    flag_columns = [
        column for column in df.columns 
        if column.startswith("is_")
    ]

    # 요약 정보 기본 구조 생성
    summary = {
        "row_count" : len(df),
        "column_count" : len(df.columns),
        "flag_columns" : flag_columns,
        "flag_summary" : {}
    }

    # 각 Flag 컬럼별 True 개수 계산
    for column in flag_columns:
        summary["flag_summary"][column] = int(df[column].sum())
    
    return summary


# preprocess_staging_dataframe: Staging DataFrame 전체 전처리 실행
def preprocess_staging_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Staging DataFrame에 전체 전처리 과정을 적용

    Args:
        df (pd.DataFrame): 컬럼 매핑이 완료된 Staging DataFrame
    
    Returns:
        tuple:
            - pd.DataFrame: 전처리 완료 DataFrame
            - dict: 전처리 결과 요약 정보
    
    Raises:
        ValueError: 입력 DataFrame이 비어 있는 경우 발생
    """

    # 입력 DataFrame이 비어 있는 경우 에러
    if df is None or df.empty:
        raise ValueError("전처리할 데이터가 없습니다.")
    
    # 원본 보존용 복사본 생성
    preprocessed_df = df.copy()

    # 문자열 기반 결측값 정규화
    preprocessed_df = normalize_missing_values(preprocessed_df)

    # 문자열 컬럼 공백 제거
    preprocessed_df = strip_string_columns(preprocessed_df)

    # 날짜 컬럼 타입 변환
    preprocessed_df = convert_date_columns(preprocessed_df)

    # 숫자 컬럼 타입 변환
    preprocessed_df = convert_numeric_columns(preprocessed_df)

    # 필수 컬럼 결측 Flag 생성
    preprocessed_df = add_missing_flags(preprocessed_df)

    # 기본 정합성 Flag 생성
    preprocessed_df = add_consistency_flags(preprocessed_df)

    # 전처리 결과 요약 생성
    preprocessing_summary = create_preprocessing_summary(preprocessed_df)

    return preprocessed_df, preprocessing_summary