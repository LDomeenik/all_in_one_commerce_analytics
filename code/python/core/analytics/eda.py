"""
eda.py

EDA 분석 모듈

기능:
    - 기초 통계 분석
    - 수치형 컬럼 기초 통계 분석
    - 문자열 컬럼 기초 통계 분석
    - 시계열 분포 분석
    - 주요 컬럼 분포 분석
"""


import pandas as pd


# _get_basic_stats: 기초 통계 분석
def _get_basic_stats(df: pd.DataFrame) -> dict:
    """
    DataFrame 의 기초 통계 정보를 반환합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame

    Returns:
        dict: 기초 통계 정보
            - row_count (int): 전체 행 수
            - column_count (int): 전체 컬럼 수
            - date_range (dict): 주문 기간 정보
                - start (str): 시작일
                - end (str): 종료일
                - days (int): 분석 기간 일수

    Raises:
        없음
    """

    # 전체 행 수, 컬럼 수 계산
    row_count = len(df)
    col_count = len(df.columns)

    # order_date 가 있는 경우 주문 기간 계산
    date_range = {}

    if "order_date" in df.columns:
        # order_date의 null값을 제외하고 계산
        valid_dates = df["order_date"].dropna()
        
        if len(valid_dates) > 0:
            min_date = valid_dates.min()
            max_date = valid_dates.max()
            start=min_date.strftime("%Y-%m-%d")
            end=max_date.strftime("%Y-%m-%d")
            days=(max_date - min_date).days
            date_range = {
                "start" : start,
                "end" : end,
                "days" : days
            }

    # 결과 반환
    return {
        "row_count": row_count,
        "column_count": col_count,
        "date_range" : date_range
    }


# _get_numeric_stats: 수치형 컬럼 기초 통계 분석
def _get_numeric_stats(df: pd.DataFrame) -> dict:
    """
    수치형 컬럼의 기초 통계를 반환합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame

    Returns:
        dict: {컬럼명: {mean, median, min, max, std, null_count}} 딕셔너리

    Raises:
        없음
    """

    # Flag 컬럼 제외한 수치형 컬럼 추출
    # is_ 로 시작하지 않는 컬럼 중 numeric, integer 타입
    numeric_cols = [
        col for col in df.columns
        if not col.startswith("is_")
        and df[col].dtype in ["float64", "int64"]
    ]

    # 컬럼별 mean, median, min, max, std, null_count 계산
    result = {}

    for col in numeric_cols:
        result[col] = {
            "mean" : df[col].mean(),
            "median" : df[col].median(),
            "min" : df[col].min(),
            "max" : df[col].max(),
            "std" : df[col].std(),
            "null_count" : df[col].isna().sum()
        }

    return result


# _get_categorical_stats: 문자열 컬럼 기초 통계 분석
def _get_categorical_stats(df: pd.DataFrame) -> dict:
    """
    문자열 컬럼의 기초 통계를 반환합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame

    Returns:
        dict: {컬럼명: {unique_count, top_value, top_count, null_count}} 딕셔너리

    Raises:
        없음
    """

    # Flag 컬럼 제외한 문자열 컬럼 추출
    categorical_cols = [
        col for col in df.columns
        if not col.startswith("is_")
        and df[col].dtype == "object"
    ]

    # 컬럼별 unique_count, top_value, top_count, null_count 계산
    result = {}

    for col in categorical_cols:
        value_counts = df[col].value_counts()
        result[col] = {
            "unique_count" : df[col].nunique(),
            "top_value" : value_counts.index[0] if len(value_counts) > 0 else None,
            "top_count" : value_counts.iloc[0] if len(value_counts) > 0 else 0,
            "null_count" : df[col].isna().sum()
        }
    
    return result


# _get_time_series: 시계열 분포 분석
def _get_time_series(df: pd.DataFrame) -> pd.DataFrame:
    """
    월별 주문 수 및 매출 추이를 반환합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame

    Returns:
        pd.DataFrame: 월별 주문 수, 매출 집계 결과
            - year_month (str): 연월 (YYYY-MM)
            - order_count (int): 주문 수
            - revenue (float): 매출 (revenue 컬럼 있는 경우)

    Raises:
        없음
    """

    # order_date 가 없으면 빈 DataFrame 반환
    if "order_date" not in df.columns:
        return pd.DataFrame()

    result_df = df.copy()

    # year_month 컬럼 생성 (YYYY-MM 형식)
    result_df["year_month"] = df["order_date"].dt.strftime("%Y-%m")

    # 월별 주문 수 집계
    # revenue 가 있으면 매출도 함께 집계
    agg_dict = {"order_id" : "nunique"}

    if "revenue" in result_df.columns:
        agg_dict["revenue"] = "sum"

    # 결과 반환
    time_series = (
        result_df
        .groupby("year_month")
        .agg(agg_dict)
        .reset_index()
        .rename(columns={"order_id" : "order_count"})
        .sort_values("year_month")
    )

    return time_series


# _get_distribution: 주요 컬럼 분포 분석
def _get_distribution(df: pd.DataFrame) -> dict:
    """
    주요 카테고리 컬럼의 분포를 반환합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame

    Returns:
        dict: {컬럼명: value_counts DataFrame} 딕셔너리
            - order_status 분포 (있는 경우)
            - product_category 분포 (있는 경우)
            - payment_method 분포 (있는 경우)

    Raises:
        없음
    """

    # 분포 분석 대상 컬럼 정의
    # order_status, product_category, payment_method
    target_cols = ["order_status", "product_category", "payment_method"]

    # 존재하는 컬럼에 대해서만 value_counts 계산
    result = {}

    for col in target_cols:
        if col in df.columns:
            result[col] = (
                df[col]
                .value_counts()
                .reset_index()
                .set_axis([col, "count"], axis=1)
            )
    
    return result


# run_eda: EDA 분석 실행
def run_eda(tables: dict[str, pd.DataFrame], column_registry: dict[str, str]) -> dict:
    """
    EDA 분석을 실행합니다.

    Args:
        tables (dict[str, pd.DataFrame]): 테이블 딕셔너리
        column_registry (dict[str, str]): {컬럼명: 테이블유형} 레지스트리

    Returns:
        dict: {테이블 유형: EDA 결과} 딕셔너리
            각 테이블별:
                - basic_stats (dict): 기초 통계
                - numeric_stats (dict): 수치형 컬럼 통계
                - categorical_stats (dict): 문자열 컬럼 통계
                - time_series (pd.DataFrame): 시계열 분포
                - distribution (dict): 주요 컬럼 분포

    Raises:
        ValueError: 입력 DataFrame 이 비어 있는 경우
    """

    # 입력 table 검증
    if not tables:
        raise ValueError("분석할 데이터가 없습니다.")

    result = {}

    # 각 테이블별로 EDA 실행
    for table_type, df in tables.items():
        # Flag 컬럼 제외한 데이터 컬럼만 사용
        data_cols = [
            col for col in df.columns
            if not col.startswith("is_")
        ]

        data_df = df[data_cols]
        
        # 각 테이블별로 집계
        result[table_type] = {
            "basic_stats": _get_basic_stats(data_df),
            "numeric_stats": _get_numeric_stats(data_df),
            "categorical_stats": _get_categorical_stats(data_df),
            "time_series": _get_time_series(data_df),
            "distribution": _get_distribution(data_df)
        }

    return result