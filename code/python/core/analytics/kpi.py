"""
kpi.py

KPI 분석 모듈

기능:
    - 매출 지표 계산 (총 매출, 당월 매출, 순매출, AOV, 당월 AOV, 전월 대비 성장률)
    - 주문 지표 계산 (총 주문 수, 당월 주문 수, 취소율, 당월 취소율, 전월 대비 성장률)
    - 고객 지표 계산 (총/당월 고객 수, 신규/재구매 고객, 재구매율, 당월 신규/재구매/재구매율, 전월 대비 성장률)
    - 월별 KPI 추이 계산 (매출, 주문 수, AOV, 고객 수, 취소율, 신규/재구매 고객, 재구매율)
"""


import pandas as pd

from core.analytics.table_selector import get_dataframe_with_columns


# _get_revenue_stats: 매출 지표 계산
def _get_revenue_stats(df: pd.DataFrame, monthly_trend: pd.DataFrame) -> dict:
    """
    매출 관련 KPI 지표를 계산합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
        monthly_trend (pd.DataFrame): 월별 추이 DataFrame

    Returns:
        dict: 매출 지표
            - total_revenue (float): 총 매출 (전체 기간 합계)
            - current_month_revenue (float | None): 당월 매출
            - net_revenue (float): 순매출
            - aov (float): 평균 주문 금액 (전체 기간)
            - current_month_aov (float | None): 당월 AOV
            - revenue_growth (float | None): 전월 대비 매출 성장률 (%)

    Raises:
        없음
    """

    total_revenue = df["revenue"].sum()
    total_orders = df["order_id"].nunique()
    aov = total_revenue / total_orders if total_orders > 0 else 0

    if "discount_amount" in df.columns:
        net_revenue = total_revenue - df["discount_amount"].sum()
    else:
        net_revenue = total_revenue

    current_month_revenue = None
    current_month_aov = None
    if len(monthly_trend) >= 1:
        current_month_revenue = monthly_trend.iloc[-1]["revenue"]
        if "aov" in monthly_trend.columns:
            current_month_aov = monthly_trend.iloc[-1]["aov"]

    revenue_growth = None
    if len(monthly_trend) >= 2:
        this_month = monthly_trend.iloc[-1]["revenue"]
        last_month = monthly_trend.iloc[-2]["revenue"]
        if last_month != 0:
            revenue_growth = (this_month - last_month) / last_month * 100

    return {
        "total_revenue": total_revenue,
        "current_month_revenue": current_month_revenue,
        "net_revenue": net_revenue,
        "aov": aov,
        "current_month_aov": current_month_aov,
        "revenue_growth": revenue_growth
    }


# _get_order_stats: 주문 지표 계산
def _get_order_stats(df: pd.DataFrame, monthly_trend: pd.DataFrame) -> dict:
    """
    주문 관련 KPI 지표를 계산합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
        monthly_trend (pd.DataFrame): 월별 추이 DataFrame

    Returns:
        dict: 주문 지표
            - total_orders (int): 총 주문 수 (전체 기간)
            - current_month_orders (int | None): 당월 주문 수
            - cancel_rate (float | None): 취소율 (전체 기간, %)
            - current_month_cancel_rate (float | None): 당월 취소율 (%)
            - order_growth (float | None): 전월 대비 주문 수 성장률 (%)

    Raises:
        없음
    """

    total_orders = df["order_id"].nunique()

    if "order_status" in df.columns:
        cancel_orders = df[
            df["order_status"].str.lower().isin(["cancelled", "canceled"])
        ]["order_id"].nunique()
        cancel_rate = cancel_orders / total_orders * 100 if total_orders > 0 else 0
    else:
        cancel_rate = None

    current_month_orders = None
    current_month_cancel_rate = None
    if len(monthly_trend) >= 1:
        current_month_orders = monthly_trend.iloc[-1]["order_count"]
        if "cancel_rate" in monthly_trend.columns:
            current_month_cancel_rate = monthly_trend.iloc[-1]["cancel_rate"]

    order_growth = None
    if len(monthly_trend) >= 2:
        this_month = monthly_trend.iloc[-1]["order_count"]
        last_month = monthly_trend.iloc[-2]["order_count"]
        if last_month != 0:
            order_growth = (this_month - last_month) / last_month * 100

    return {
        "total_orders": total_orders,
        "current_month_orders": current_month_orders,
        "cancel_rate": cancel_rate,
        "current_month_cancel_rate": current_month_cancel_rate,
        "order_growth": order_growth
    }


# _get_customer_stats: 고객 지표 계산
def _get_customer_stats(df: pd.DataFrame, monthly_trend: pd.DataFrame) -> dict:
    """
    고객 관련 KPI 지표를 계산합니다.
    customer_id 컬럼이 없으면 빈 딕셔너리를 반환합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
        monthly_trend (pd.DataFrame): 월별 추이 DataFrame

    Returns:
        dict: 고객 지표
            - total_customers (int): 총 고객 수 (전체 기간)
            - current_month_customers (int | None): 당월 고객 수
            - new_customers (int): 신규 고객 수 (전체 기간 기준 1회 구매 고객)
            - repeat_customers (int): 재구매 고객 수 (전체 기간 기준 2회 이상 구매 고객)
            - repeat_rate (float): 재구매율 (전체 기간, %)
            - current_month_new_customers (int | None): 당월 신규 고객 수
            - current_month_repeat_customers (int | None): 당월 재구매 고객 수
            - current_month_repeat_rate (float | None): 당월 재구매율 (%)
            - customer_growth (float | None): 전월 대비 고객 수 성장률 (%)

    Raises:
        없음
    """

    if "customer_id" not in df.columns:
        return {}

    customer_order_counts = (
        df.groupby("customer_id")["order_id"].nunique()
    )

    total_customers = df["customer_id"].nunique()
    new_customers = (customer_order_counts == 1).sum()
    repeat_customers = (customer_order_counts >= 2).sum()
    repeat_rate = repeat_customers / total_customers * 100 if total_customers > 0 else 0

    current_month_customers = None
    current_month_new_customers = None
    current_month_repeat_customers = None
    current_month_repeat_rate = None

    if len(monthly_trend) >= 1:
        if "customer_count" in monthly_trend.columns:
            current_month_customers = monthly_trend.iloc[-1]["customer_count"]
        if "new_customers" in monthly_trend.columns:
            current_month_new_customers = monthly_trend.iloc[-1]["new_customers"]
        if "repeat_customers" in monthly_trend.columns:
            current_month_repeat_customers = monthly_trend.iloc[-1]["repeat_customers"]
        if "repeat_rate" in monthly_trend.columns:
            current_month_repeat_rate = monthly_trend.iloc[-1]["repeat_rate"]

    customer_growth = None
    if len(monthly_trend) >= 2 and "customer_count" in monthly_trend.columns:
        this_month = monthly_trend.iloc[-1]["customer_count"]
        last_month = monthly_trend.iloc[-2]["customer_count"]
        if last_month != 0:
            customer_growth = (this_month - last_month) / last_month * 100

    return {
        "total_customers": total_customers,
        "current_month_customers": current_month_customers,
        "new_customers": new_customers,
        "repeat_customers": repeat_customers,
        "repeat_rate": repeat_rate,
        "current_month_new_customers": current_month_new_customers,
        "current_month_repeat_customers": current_month_repeat_customers,
        "current_month_repeat_rate": current_month_repeat_rate,
        "customer_growth": customer_growth
    }


# _get_monthly_trend: 월별 KPI 추이 계산
def _get_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    월별 KPI 추이를 계산합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame

    Returns:
        pd.DataFrame: 월별 KPI 추이
            - year_month (str): 연월 (YYYY-MM)
            - order_count (int): 월별 주문 수
            - revenue (float): 월별 매출
            - aov (float): 월별 AOV
            - customer_count (int): 월별 고객 수 (customer_id 있는 경우)
            - cancel_rate (float): 월별 취소율 (order_status 있는 경우)
            - new_customers (int): 월별 신규 고객 수 (customer_id 있는 경우)
            - repeat_customers (int): 월별 재구매 고객 수 (customer_id 있는 경우)
            - repeat_rate (float): 월별 재구매율 (customer_id 있는 경우)

    Raises:
        없음
    """

    if "order_date" not in df.columns:
        return pd.DataFrame()

    result_df = df.copy()
    result_df["year_month"] = result_df["order_date"].dt.strftime("%Y-%m")

    agg_dict = {"order_id": "nunique"}

    if "revenue" in result_df.columns:
        agg_dict["revenue"] = "sum"

    if "customer_id" in result_df.columns:
        agg_dict["customer_id"] = "nunique"

    monthly = (
        result_df.groupby("year_month")
        .agg(agg_dict)
        .reset_index()
        .rename(columns={
            "order_id": "order_count",
            "customer_id": "customer_count"
        })
        .sort_values("year_month")
        .reset_index(drop=True)
    )

    if "revenue" in monthly.columns:
        monthly["aov"] = monthly["revenue"] / monthly["order_count"]

    if "order_status" in result_df.columns:
        cancel_monthly = (
            result_df[
                result_df["order_status"].str.lower().isin(["cancelled", "canceled"])
            ]
            .groupby("year_month")["order_id"]
            .nunique()
            .reset_index()
            .rename(columns={"order_id": "cancel_count"})
        )
        monthly = monthly.merge(cancel_monthly, on="year_month", how="left")
        monthly["cancel_count"] = monthly["cancel_count"].fillna(0)
        monthly["cancel_rate"] = monthly["cancel_count"] / monthly["order_count"] * 100

    if "customer_id" in result_df.columns:

        first_purchase = (
            result_df.groupby("customer_id")["year_month"]
            .min()
            .reset_index()
            .rename(columns={"year_month": "first_month"})
        )

        result_df = result_df.merge(first_purchase, on="customer_id", how="left")

        new_customers_monthly = (
            result_df[result_df["year_month"] == result_df["first_month"]]
            .groupby("year_month")["customer_id"]
            .nunique()
            .reset_index()
            .rename(columns={"customer_id": "new_customers"})
        )

        repeat_customers_monthly = (
            result_df[result_df["year_month"] != result_df["first_month"]]
            .groupby("year_month")["customer_id"]
            .nunique()
            .reset_index()
            .rename(columns={"customer_id": "repeat_customers"})
        )

        monthly = monthly.merge(new_customers_monthly, on="year_month", how="left")
        monthly = monthly.merge(repeat_customers_monthly, on="year_month", how="left")
        monthly["new_customers"] = monthly["new_customers"].fillna(0)
        monthly["repeat_customers"] = monthly["repeat_customers"].fillna(0)

        monthly["repeat_rate"] = (
            monthly["repeat_customers"] / monthly["customer_count"] * 100
        )

    return monthly


# run_kpi: KPI 분석 실행
def run_kpi(tables: dict[str, pd.DataFrame], column_registry: dict[str, str]) -> dict:
    """
    KPI 분석을 실행합니다.

    Args:
        tables (dict[str, pd.DataFrame]): 테이블 딕셔너리
        column_registryt (dict[str, str]): {컬럼명: 테이블유형} 레지스트리

    Returns:
        dict: KPI 분석 결과
            - revenue_stats (dict): 매출 지표
            - order_stats (dict): 주문 지표
            - customer_stats (dict): 고객 지표
            - monthly_trend (pd.DataFrame): 월별 KPI 추이

    Raises:
        ValueError: 입력 DataFrame 이 비어 있는 경우
    """

    # 필요한 컬럼을 가진 테이블 자동 선택
    df = get_dataframe_with_columns(
        tables,
        column_registry,
        required=[
            "order_id", "order_date", "revenue", "order_status", "customer_id", "discount_amount"
        ],
        agg={"revenue":"sum", "discount_amount":"sum"}
    )

    # 입력 DataFrame 검증
    if df is None or df.empty:
        raise ValueError("KPI 분석에 필요한 order 테이블이 없습니다.")

    # Flag 컬럼을 제외한 컬럼만 추출
    data_columns = [
        col for col in df.columns
        if not col.startswith("is_")
    ]

    data_df = df[data_columns]

    # 월별 추이 계산
    monthly_trend = _get_monthly_trend(data_df)

    # 매출 지표 계산
    revenue_stats = _get_revenue_stats(data_df, monthly_trend)

    # 주문 지표 계산
    order_stats = _get_order_stats(data_df, monthly_trend)

    # 고객 지표 계산
    customer_stats = _get_customer_stats(data_df, monthly_trend)

    return {
        "revenue_stats": revenue_stats,
        "order_stats": order_stats,
        "customer_stats": customer_stats,
        "monthly_trend": monthly_trend
    }