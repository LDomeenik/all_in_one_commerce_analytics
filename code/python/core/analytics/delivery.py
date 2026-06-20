"""
delivery.py

배송/운영 분석 모듈

기능:
    - 핵심 배송 지표 계산 (평균 배송 소요일, 완료율, 지연율)
    - 배송 소요일 구간별 분포 계산
    - 월별 배송 추이 계산
"""


import pandas as pd


# _get_delivery_stats: 핵심 배송 지표 계산
def _get_delivery_stats(df: pd.DataFrame) -> dict:
    """
    핵심 배송 지표를 계산합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
    
    Returns:
        dict:
            - avg_total_lead_time (float): 평균 주문 → 도착 소요일
            - avg_shipping_lead_time (float | None): 평균 주문 → 출고 소요일
            - avg_delivery_lead_time (float | None): 평균 출고 → 도착 소요일
            - delivery_complete_rate (float | None): 배송 완료율 (%)
            - delivery_delay_rate (float | None): 배송 지연율 (%)

    Raises:
        없음
    """

    # 평균 주문 → 도착 소요일
    total_lead_time = (
        df["delivered_date"] - df["order_date"]
    ).dt.days

    avg_total_lead_time = total_lead_time.mean()

    # 평균 주문 → 출고 소요일
    avg_shipping_lead_time = None

    if "shipped_date" in df.columns:
        shipping_lead_time = (
            df["shipped_date"] - df["order_date"]
        ).dt.days
        avg_shipping_lead_time = shipping_lead_time.mean()
    
    # 평균 출고 → 도착 소요일
    avg_delivery_lead_time = None

    if "delivery_days" in df.columns:
        avg_delivery_lead_time = df["delivery_days"].mean()
    
    # 배송 완료율
    delivery_complete_rate = None

    if "order_status" in df.columns:
        total_orders = df["order_id"].nunique()
        delivered_orders = df[
            df["order_status"].str.lower() == "delivered"
        ]["order_id"].nunique()

        delivery_complete_rate = delivered_orders / total_orders * 100.0
    
    # 배송 지연율
    delivery_delay_rate = None

    if "estimated_delivery_date" in df.columns:
        valid = df[
            df["delivered_date"].notna()
            & df["estimated_delivery_date"].notna()
        ]

        if len(valid) > 0:
            delayed = valid[
                valid["delivered_date"] > valid["estimated_delivery_date"]
            ]

            delivery_delay_rate = len(delayed) / len(valid) * 100.0
    
    # 결과 반환
    return {
        "avg_total_lead_time" : avg_total_lead_time,
        "avg_shipping_lead_time" : avg_shipping_lead_time,
        "avg_delivery_lead_time" : avg_delivery_lead_time,
        "delivery_complete_rate" : delivery_complete_rate,
        "delivery_delay_rate" : delivery_delay_rate
    }


# _get_delivery_distribution: 배송 소요일 구간별 분포 계산
def _get_delivery_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    주문 → 도착 소요일 구간별 주문 수와 비율을 계산합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
    
    Returns:
        pd.DataFrame: 구간별 분포
            - range (str): 소요일 구간
            - order_count (int): 주문 수
            - pct (float): 비율 (%)
    
    Raises:
        없음
    """

    # 주문 → 도착 소요일 계산
    total_lead_time = (
        df["delivered_date"] - df["order_date"]
    ).dt.days.dropna()

    # 구간 분류 내부 함수
    def _classify_range(days):
        if days <= 1:
            return "1일 이내"
        elif days <= 3:
            return "2~3일"
        elif days <= 7:
            return "4~7일"
        else:
            return "8일 이상"
    
    # 각 주문의 소요일을 구간으로 변환 후 집계
    range_series = total_lead_time.apply(_classify_range)
    range_counts = range_series.value_counts()

    # 순서 고정
    order = ["1일 이내", "2~3일", "4~7일", "8일 이상"]

    # 집계
    distribution = pd.DataFrame(
        {
            "range" : order,
            "order_count" : [range_counts.get(r, 0) for r in order]
        }
    )

    # 비율 계산
    total = distribution["order_count"].sum()
    distribution["pct"] = distribution["order_count"] / total * 100.0

    # 결과 반환
    return distribution


# _get_monthly_delivery: 월별 배송 추이 계산
def _get_monthly_delivery(df: pd.DataFrame) -> pd.DataFrame:
    """
    월별 평균 배송 소요일 및 지연율 추이를 계산합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
    
    Returns:
        pd.DataFrame: 월별 배송 추이
            - year_month (str): 연월 (YYYY-MM)
            - avg_lead_time (float): 월별 평균 주문 → 도착 소요일
            - delay_rate (float | None): 월별 배송 지연율 (%)
    
    Raises:
        없음
    """

    result_df = df.copy()

    # year_month 컬럼 생성
    result_df["year_month"] = result_df["order_date"].dt.strftime("%Y-%m")

    # 주문 → 도착 소요일 컬럼 생성
    result_df["total_lead_time"] = (
        result_df["delivered_date"] - result_df["order_date"]
    ).dt.days

    # 월별 평균 배송 소요일 집계
    monthly = (
        result_df.groupby("year_month")
        .agg(avg_lead_time=("total_lead_time", "mean"))
        .reset_index()
        .sort_values("year_month")
    )

    # 월별 배송 지연율 추가
    if "estimated_delivery_date" in result_df.columns:
        delay_monthly = (
            result_df[
                result_df["delivered_date"].notna()
                & result_df["estimated_delivery_date"].notna()
            ]
            .assign(is_delayed=lambda x: x["delivered_date"] > x["estimated_delivery_date"])
            .groupby("year_month")["is_delayed"]
            .mean() * 100
        ).reset_index().rename(columns={"is_delayed": "delay_rate"})

        monthly = monthly.merge(delay_monthly, on="year_month", how="left")
    
    return monthly


# run_delivery: 배송/운영 분석 실행
def run_delivery(df: pd.DataFrame) -> dict:
    """
    배송/운영 분석을 실행합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
    
    Returns:
        dict: 배송/운영 분석 결과
            - delivery_state (dict): 핵심 배송 지표
            - delivery_distribution (pd.DataFrame): 배송 소요일 구간별 분포
            - monthly_delivery (pd.DataFrame): 월별 배송 추이
    
    Raises:
        ValueError: 입력 DataFrame이 비어 있는 경우
    """

    # 입력 DataFrame 검증
    if df is None or df.empty:
        raise ValueError("분석할 데이터가 없습니다.")
    
    # Flag 컬럼 제외한 데이터 컬럼만 사용
    data = [
        col for col in df.columns
        if not col.startswith("is_")
    ]

    data_df = df[data]

    # delivered_date가 있는 행만 사용
    delivered_df = data_df[data_df["delivered_date"].notna()]

    # 핵심 배송 지표 계산
    delivery_stats = _get_delivery_stats(data_df)

    # 배송 소요일 구간별 분포 계산
    delivery_distribution = _get_delivery_distribution(delivered_df)

    # 월별 배송 추이 계산
    monthly_delivery = _get_monthly_delivery(delivered_df)

    # 결과 반환
    return {
        "delivery_stats" : delivery_stats,
        "delivery_distribution" : delivery_distribution,
        "monthly_delivery" : monthly_delivery
    }