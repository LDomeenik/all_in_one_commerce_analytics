"""
cohort.py

코호트 분석 모듈

기능:
    - 고객별 첫 구매 월 계산
    - 코호트별 월별 재구매 고객 수 집계
    - 코호트 retention matrix 생성
    - 코호트 retention rate matrix 생성
"""


import pandas as pd

from core.analytics.table_selector import get_dataframe_with_columns


# _get_first_purchase_month: 고객별 첫 구매 월 계산
def _get_first_purchase_month(df: pd.DataFrame) -> pd.DataFrame:
    """
    고객별 첫 구매월을 계산합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
    
    Returns:
        pd.DataFrame: 고객별 첫 구매 월 정보
            - customer_id (str): 고객 ID
            - cohort_month (str): 첫 구매 월 (YYYY-MM)
    
    Raises:
        없음
    """

    # customer_id 기준으로 order_date 최솟값 계산
    first_purchase = (
        df.groupby("customer_id")["order_date"]
        .min()
        .reset_index()
        .rename(columns={"order_date" : "cohort_month"})
    )

    # cohort_month YYYY-MM 형식 변환
    first_purchase["cohort_month"] = first_purchase["cohort_month"].dt.strftime("%Y-%m")

    # 결과 반환
    return first_purchase


# _build_cohort_matrix: 코호트 retention matrix 생성
def _build_cohort_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    코호트별 월별 재구매 고객 수 matrix를 생성합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
    
    Returns:
        pd.DataFrame: 코호트 matrix
            - index: cohort_month (첫 구매 월)
            - columns: period (0, 1, 2, ... 경과 월 수)
            - values: 해당 월에 구매한 고객 수
    
    Raises:
        없음
    """

    # 고객별 첫 구매 월 계산
    first_purchase = _get_first_purchase_month(df)

    # 원본 df에 cohort_month 병합
    result_df = df.merge(first_purchase, on="customer_id", how="left")

    # order_date에서 order_month 생성 (YYYY-MM)
    result_df["order_month"] = result_df["order_date"].dt.strftime("%Y-%m")

    # 경과 월 수(period) 계산
    order_dt = pd.to_datetime(result_df["order_month"])
    cohort_dt = pd.to_datetime(result_df["cohort_month"])

    result_df["period"] = (order_dt.dt.year - cohort_dt.dt.year) * 12 + (order_dt.dt.month - cohort_dt.dt.month)

    # cohort_month, period 기준으로 고유 고객 수 집계
    cohort_matrix = (
        result_df.groupby(["cohort_month", "period"])["customer_id"]
        .nunique()
        .reset_index()
        .pivot(index="cohort_month", columns="period", values="customer_id")
    )

    # 결과 반환
    return cohort_matrix


# _build_retention_rate_matrix: retention rate matrix 생성
def _build_retention_rate_matrix(cohort_matrix: pd.DataFrame) -> pd.DataFrame:
    """
    코호트 retention rate matrix를 생성합니다.

    Args:
        cohort_matrix (pd.DataFrame): 코호트 고객 수 matrix
    
    Returns:
        pd.DataFrame: retention rate matrix (%)
            - index: cohort_month
            - columns: period
            - values: 0월 대비 재구매율 (%)
    
    Raises:
        없음
    """

    # 0월 (첫 구매 월) 고객 수를 기준으로 각 period의 비율 계산
    retention_rate = cohort_matrix.div(cohort_matrix[0], axis=0) * 100

    # 결과 반환
    return retention_rate


# run_cohort: 코호트 분석 실행
def run_cohort(tables: dict[str, pd.DataFrame], column_registry: dict[str, str]) -> dict:
    """
    코호트 분석을 실행합니다.

    Args:
        tables (dict[str, pd.DataFrame]): 테이블 딕셔너리
        column_registry (dict[str, str]): {컬럼명: 테이블유형} 레지스트리
    
    Returns:
        dict: 코호트 분석 결과
            - cohort_matrix (pd.DataFrame): 코호트별 월별 고객 수 matrix
            - retention_rate_matrix (pd.DataFrame): 코호트별 retention rate matrix (%)
    
    Raises:
        ValueError: 입력 DataFrame 이 비어 있는 경우
    """

    # 필요한 컬럼을 가진 테이블 자동 선택
    df = get_dataframe_with_columns(
        tables,
        column_registry,
        required=[
            "customer_id", "order_date", "order_id"
        ]
    )

    # 입력 DataFrame 검증
    if df is None or df.empty:
        raise ValueError("분석할 데이터가 없습니다.")
    
    # Flag 컬럼을 제외한 데이터 컬럼만 사용
    data_columns = [
        col for col in df.columns
        if not col.startswith("is_")
    ]

    data_df = df[data_columns]
    
    # 코호트 matrix 생성
    cohort_matrix = _build_cohort_matrix(data_df)

    # retention rate matrix 생성
    retention_rate_matrix = _build_retention_rate_matrix(cohort_matrix)

    # 결과 반환
    return {
        "cohort_matrix" : cohort_matrix,
        "retention_rate_matrix" : retention_rate_matrix
    }