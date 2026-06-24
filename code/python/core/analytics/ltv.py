"""
ltv.py

고객 생애 가치(LTV) 분석 모듈

기능:
    - 평균 기반 LTV 계산 (AOV x 구매 빈도 x 평균 고객 수명)
    - 코호트 기반 누적 LTV 계산
    - BG.NBD + Gamma-Gamma 모델 기반 예측 LTV 계산
"""


import pandas as pd
import numpy as np


# calculate_average_ltv: AOV x 구매 빈도 x 평균 고객 수명으로 LTV 계산
def calculate_average_ltv(df: pd.DataFrame) -> dict:
    """
    평균 기반 LTV를 계산합니다.
    LTV = AOV x 구매 빈도 x 평균 고객 수명(년)

    Args:
        df (pd.DataFrame): order_id, customer_id, order_date, revenue 컬럼 포함 DataFrame
    
    Returns:
        dict:
            - metrics (dict): aov, purchase_frequency, avg_lifespan_days, ltv
            - customer_df (pd.DataFrame): 고객별 집계 데이터
    """

    # 고객별 집계
    customer_df = df.groupby("customer_id").agg(
        order_count=("order_id", "nunique"),
        total_revenue=("revenue", "sum"),
        first_order=("order_date", "min"),
        last_order=("order_date", "max")
    ).reset_index()

    # 고객 수명 계산
    customer_df["lifespan_days"] = (
        customer_df["last_order"] - customer_df["first_order"]
    ).dt.days

    # 전체 지표 계산
    total_revenue = customer_df["total_revenue"].sum()
    total_orders = customer_df["order_count"].sum()
    total_customers = len(customer_df)

    aov = total_revenue / total_orders
    purchase_frequency = total_orders / total_customers

    # 재구매 고객만으로 평균 수명 계산
    repeat_customers = customer_df[customer_df["lifespan_days"] > 0]
    avg_lifespan_days = repeat_customers["lifespan_days"].mean() if len(repeat_customers) > 0 else 0.0

    # LTV 계산
    ltv = aov * purchase_frequency * (avg_lifespan_days/365)

    # 고객별 LTV 컬럼 추가
    customer_df["customer_ltv"] = customer_df["total_revenue"]

    # 결과 반환
    return {
        "metrics": {
            "aov": round(aov, 2),
            "purchase_frequency": round(purchase_frequency, 2),
            "avg_lifespan_days": round(avg_lifespan_days, 1),
            "ltv": round(ltv, 2)
        },
        "customer_df": customer_df
    }


# calculate_cohort_ltv: 코호트별 누적 LTV 계산
def calculate_cohort_ltv(df: pd.DataFrame) -> dict:
    """
    코호트 기반 누적 LTV를 계산합니다.
    첫 구매 월 기준 코호트별로 시간에 따른 누적 매출을 고객 1인당으로 정규화합니다.

    Args:
        df (pd.DataFrame): order_id, customer_id, order_date, revenue 컬럼 포함 DataFrame
    
    Returns:
        dict:
            - cohort_ltv_df (pd.DataFrame): cohort_month, period, cumulative_ltv_per_customer
            - cohort_size_df (pd.DataFrame): cohort_month, cohort_size
    
    Raises:
        없음
    """

    # 원본 보존용 복사본 생성
    cohort_df = df.copy()

    # 고객별 첫 구매 월 계산
    cohort_map = cohort_df.groupby("customer_id")["order_date"].min()
    cohort_map = cohort_map.dt.to_period("M")
    cohort_map.name = "cohort_month"

    # 원본 df에 cohort_month 추가
    cohort_df = cohort_df.join(cohort_map, on="customer_id")

    # 주문 월 계산
    cohort_df["order_month"] = cohort_df["order_date"].dt.to_period("M")

    # 경과 월 계산
    cohort_df["period"] = (cohort_df["order_month"] - cohort_df["cohort_month"]).apply(lambda x: x.n)

    # 코호트 x 경과 월 기준 매출 집계
    cohort_revenue = cohort_df.groupby(["cohort_month", "period"]).agg(
        revenue=("revenue", "sum")
    ).reset_index()

    # 코호트별 고객 수 계산
    cohort_size = cohort_df.groupby("cohort_month")["customer_id"].nunique()
    cohort_size.name = "cohort_size"

    # 누적 매출 계산
    cohort_revenue["cumulative_revenue"] = cohort_revenue.groupby("cohort_month")["revenue"].cumsum()

    # 고객 1인당 누적 LTV로 정규화
    cohort_revenue = cohort_revenue.join(cohort_size, on="cohort_month")
    cohort_revenue["cumulative_ltv_per_customer"] = (
        cohort_revenue["cumulative_revenue"] / cohort_revenue["cohort_size"]
    )

    # 결과 반환
    return {
        "cohort_ltv_df": cohort_revenue[["cohort_month", "period", "cumulative_ltv_per_customer"]],
        "cohort_size_df": cohort_size.reset_index()
    }


# calculate_predicted_ltv: BG/NBD + Gamma-Gamma 모델로 고객별 예측 LTV 계산
def calculate_predicted_ltv(df: pd.DataFrame, months: int = 12) -> dict:
    """
    BG/NBD + Gamma-Gamma 모델을 사용해 고객별 예측 LTV를 계산합니다.

    Args:
        df (pd.DataFrame): order_id, customer_id, order_date, revenue 컬럼 포함 DataFrame
        months (int): 예측 기간 (월 단위, 기본값 12개월)
    
    Returns:
        dict:
            - predicted_df (pd.DataFrame): 고객별 예측 LTV
            - total_predicted_ltv (float): 전체 고객 예측 LTV 합계
            - avg_predicted_ltv (float): 고객 1인당 평균 예측 LTV
            - bgf: BetaGeoFitter 객체
            - summary (pd.DataFrame): 요약 데이터
    
    Raises:
        없음
    """

    from lifetimes import BetaGeoFitter, GammaGammaFitter
    from lifetimes.utils import summary_data_from_transaction_data

    # 고객별 요약 데이터 생성
    summary = summary_data_from_transaction_data(
        df,
        customer_id_col="customer_id",
        datetime_col="order_date",
        monetary_value_col="revenue",
        observation_period_end=df["order_date"].max()
    )

    # BG/NBD 모델 학습
    bgf = BetaGeoFitter(penalizer_coef=0.01)
    bgf.fit(
        summary["frequency"],
        summary["recency"],
        summary["T"]
    )

    # 예측 기간 내 구매 횟수 예측
    summary["predicted_purchases"] = bgf.predict(
        months * 30,
        summary["frequency"],
        summary["recency"],
        summary["T"]
    )

    # Gamma-Gamma 모델 학습
    ggf_data = summary[summary["frequency"] >= 1]

    ggf = GammaGammaFitter(penalizer_coef=0.01)
    ggf.fit(
        ggf_data["frequency"],
        ggf_data["monetary_value"]
    )

    # 예측 LTV 계산
    summary["predicted_ltv"] = ggf.customer_lifetime_value(
        bgf,
        summary["frequency"],
        summary["recency"],
        summary["T"],
        summary["monetary_value"],
        time=months,
        freq="D"
    )

    # 결과 데이터셋
    predicted_df = summary[["predicted_purchases", "predicted_ltv"]].reset_index()

    # 결과 반환
    return {
        "predicted_df": predicted_df,
        "total_predicted_ltv": round(predicted_df["predicted_ltv"].sum(), 2),
        "avg_predicted_ltv": round(predicted_df["predicted_ltv"].mean(), 2),
        "bgf": bgf,
        "summary": summary
    }


# validate_predicted_ltv: hold-out 방식으로 BG/NBD 예측 성능 검증
def validate_predicted_ltv(df: pd.DataFrame, bgf, summary: pd.DataFrame, train_ratio: float = 0.75) -> dict:
    """
    Hold-out 검증으로 BG/NBD 모델의 예측 성능을 평가합니다.
    전체 기간을 train_ratio 기준으로 분할하여 학습/검증 기간을 나눕니다.

    Args:
        df (pd.DataFrame): 전체 주문 데이터
        bgf: calculate_predicted_ltv에서 반환된 BetaGeoFitter 객체 (고객 목록 참조용)
        summary (pd.DataFrame): calculate_predicted_ltv에서 반환된 요약 데이터
        train_ratio (float): 학습 기간 비율 (기본값: 0.75)
    
    Returns:
        dict:
            - mae (float): 평균 절대 오차
            - rmse (float): 평균 제곱근 오차
            - mape (float): 평균 절대 백분율 오차
            - passed (bool): 검증 통과 여부 (MAPE < 30%)
            - validation_df (pd.DataFrame): 고객별 실제 vs 예측 구매 횟수
            - train_period (tuple): 학습 기간 (시작일, 종료일)
            - val_period (tuple): 검증 기간 (시작일, 종료일)
    
    Raises:
        없음
    """

    from lifetimes import BetaGeoFitter
    from lifetimes.utils import summary_data_from_transaction_data

    # 기간 분할
    min_date = df["order_date"].min()
    max_date = df["order_date"].max()
    total_days = (max_date - min_date).days

    train_end = min_date + pd.Timedelta(days=int(total_days * train_ratio))

    train_df = df[df["order_date"] <= train_end]
    val_df = df[df["order_date"] > train_end]

    # 학습 기간 summary 생성
    train_summary = summary_data_from_transaction_data(
        train_df,
        customer_id_col="customer_id",
        datetime_col="order_date",
        monetary_value_col="revenue",
        observation_period_end=train_end
    )

    # BG/NBD 재학습
    bgf_val = BetaGeoFitter(penalizer_coef=0.01)
    bgf_val.fit(
        train_summary["frequency"],
        train_summary["recency"],
        train_summary["T"]
    )

    # 검증 기간 일수 계산
    val_days = (max_date - train_end).days

    # 검증 기간 예측 구매 횟수
    train_summary["predicted_purchases"] = bgf_val.predict(
        val_days,
        train_summary["frequency"],
        train_summary["recency"],
        train_summary["T"]
    )

    # 검증 기간 실제 구매 횟수 집계
    actual = val_df.groupby("customer_id")["order_id"].nunique().rename("actual_purchases")

    # 실제와 예측 비교
    validation_df = train_summary[["predicted_purchases"]].join(actual, how="inner")
    validation_df["actual_purchases"] = validation_df["actual_purchases"].fillna(0)

    # 오차 지표 계산
    errors = validation_df["actual_purchases"] - validation_df["predicted_purchases"]
    mae = round(errors.abs().mean(), 4)
    rmse = round((errors ** 2).mean() ** 0.5, 4)
    mape = round(mae / validation_df["actual_purchases"].mean() * 100, 2)

    # 검증 통과 여부
    passed = mape < 30

    # 결과 반환
    return {
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "passed": passed,
        "validation_df": validation_df,
        "train_period": (str(min_date.date()), str(train_end.date())),
        "val_period": (str((train_end + pd.Timedelta(days=1)).date()), str(max_date.date()))
    }