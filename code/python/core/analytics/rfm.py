"""
rfm.py

RFM 분석 모듈

기능:
    - 고객별 Recency, Frequency, Monetary 계산
    - RFM 점수화 (1~5점)
    - 세그먼트별 고객 수 집계
"""


import pandas as pd

from core.analytics.table_selector import get_dataframe_with_columns


# _calculate_rfm: 고객별 RFM 값 계산
def _calculate_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """
    고객별 Recency, Frequency, Monetary를 계산합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
    
    Returns:
        pd.DataFrame: 고객별 RFM 값
            - customer_id (str): 고객 ID
            - recency (int): 마지막 구매로부터 경과일
            - frequency (int): 구매 횟수 (고유 order_id 수)
            - monetary (float): 총 구매 금액
    
    Raises:
        없음
    """

    # 분석 기준일 설정 (데이터 내 가장 최근 order_date를 기준일로 사용)
    reference_date = df["order_date"].max()

    # 고객별 RFM 집계
    rfm_df = (
        df.groupby("customer_id")
        .agg(
            recency=("order_date", "max"),
            frequency=("order_id", "nunique"),
            monetary=("revenue", "sum")
        )
        .reset_index()
    )

    # recency 재집계(기준일 - 마지막 구매일)
    rfm_df["recency"] = (reference_date - rfm_df["recency"]).dt.days

    # 결과 반환
    return rfm_df


# _score_rfm: RFM 값을 1~5점으로 점수화
def _score_rfm(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    RFM 값을 quantile 기준으로 1~5점으로 점수화힙니다. (높은 점수일수록 좋은 지표)

    Args:
        rfm_df (pd.DataFrame): 고객별 RFM 값
    
    Returns:
        pd.DataFrame: RFM 점수가 추가된 DataFrame
            - r_score (int): Recency 점수 (1~5, 최근일수록 높은 점수)
            - f_score (int): Frequency 점수 (1~5, 많을수록 높은 점수)
            - m_score (int): Monetary 점수 (1~5, 많을수록 높은 점수)
    
    Raises:
        없음
    """

    result_df = rfm_df.copy()

    # 고유값이 q보다 적을 경우 분위수를 자동 조정하는 내부 함수
    def safe_qcut(series, q, labels):

        n_unique = series.nunique()
        
        if n_unique < 2:
            mid = labels[len(labels) // 2]

            return pd.Series([mid] * len(series), index=series.index)

        actual_q = min(n_unique, q)

        _, bins = pd.qcut(series, q=actual_q, duplicates="drop", retbins=True)

        actual_bin_count = len(bins) - 1

        actual_labels = labels[:actual_bin_count]
        
        return pd.qcut(series, q=actual_q, labels=actual_labels, duplicates="drop")

    # r_score: recency가 낮을수록(최근일수록) 높은 점수
    result_df["r_score"] = safe_qcut(result_df["recency"], 5, [5, 4, 3, 2, 1])

    # f_score: frequency가 높을수록 높은 점수
    result_df["f_score"] = safe_qcut(result_df["frequency"], 5, [1, 2, 3, 4, 5])

    # m_score: monetary가 높을수록 높은 점수
    result_df["m_score"] = safe_qcut(result_df["monetary"],  5, [1, 2, 3, 4, 5])

    # 결과 반환
    return result_df


# _assign_segment: RFM 점수 조합으로 세그먼트 분류
def _assign_segment(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    RFM 점수 조합을 기준으로 고객 세그먼트를 분류합니다.

    분류 기준:
        - 최우수 고객: r_score >= 4, f_score >= 4, m_score >= 4
        - 충성 고객: r_score >= 3, f_score >= 3
        - 잠재 우수 고객: r_score >= 4, f_score <= 2
        - 신규 고객: r_score >= 4, f_score == 1, m_score == 1
        - 이탈 위험 고객: r_score == 2, f_score >= 2
        - 이탈 고객: r_score <= 2, f_score <= 2, m_score <= 2
        - 기타 고객: 위 조건에 해당되지 않는 나머지

    Args:
        rfm_df (pd.DataFrame): r_score, f_score, m_score가 포함된 DataFrame
    
    Returns:
        pd.DataFrame: segment 컬럼이 추가된 DataFrame
    
    Raises:
        없음
    """

    result_df = rfm_df.copy()

    # _claasify: 한 행의 r/f/m 점수를 받아 세그먼트 이름을 반환하는 내부 함수
    def _classify(row):
        r = int(row["r_score"])
        f = int(row["f_score"])
        m = int(row["m_score"])

        if r >= 4 and f >= 4 and m >= 4:
            return "최우수 고객"
        elif r >= 3 and f >= 3:
            return "충성 고객"
        elif r >= 4 and f <= 2:
            return "잠재 우수 고객"
        elif r >= 4 and f == 1 and m == 1:
            return "신규 고객"
        elif r == 2 and f >= 2:
            return "이탈 위험 고객"
        elif r <= 2 and f <= 2 and m <= 2:
            return "이탈 고객"
        else:
            return "기타 고객"
    
    # 내부 함수 적용
    result_df["segment"] = result_df.apply(_classify, axis=1)

    # 결과 반환
    return result_df


# _get_segment_summary: 세그먼트별 요약 통계 집계
def _get_segment_summary(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    세그먼트별 고객 수, 비율, 평균 RFM 값, 총 매출을 집계합니다.

    Args:
        rfm_df (pd.DataFrame): segment 컬럼이 포함된 RFM DataFrame
    
    Returns:
        pd.DataFrame: 세그먼트별 요약
            - segment (str): 세그먼트 이름
            - customer_count (int): 고객 수
            - customer_pct (float): 전체 고객 대비 비율 (%)
            - avg_recency (float): 평균 recency
            - avg_frequency (float): 평균 frequency
            - avg_monetary (float): 평균 monetary
            - total_monetary (float): 세그먼트 총 매출
    
    Raises:
        없음
    """

    # 전체 고객 수
    total_customers = rfm_df["customer_id"].nunique()

    # segment 기준으로 집계
    summary = (
        rfm_df.groupby("segment")
        .agg(
            customer_count=("customer_id", "nunique"),
            avg_recency=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            total_monetary=("monetary", "sum")
        )
        .reset_index()
    )

    # customer_pct
    summary["customer_pct"] = summary["customer_count"] / total_customers * 100

    # 결과 반환
    return summary


# run_rfm: RFM 분석 실행
def run_rfm(tables: dict[str, pd.DataFrame], column_registry: dict[str, str]) -> dict:
    """
    RFM 분석을 실행합니다.

    Args:
        tables (dict[str, pd.DataFrame]): 테이블 딕셔너리
        column_registry (dict[str, str]): {컬럼명: 테이블유형} 레지스트리
    
    Returns:
        dict: RFM 분석 결과
            - rfm_df (pd.DataFrame): 고객별 RFM 값, 점수, 세그먼트
            - segment_summary (pd.DataFrame): 세그먼트별 요약 통계
    
    Raises:
        ValueError: 입력 DataFrame 이 비어 있는 경우
    """

    # 필요한 컬럼을 가진 테이블 자동 선택
    df = get_dataframe_with_columns(
        tables,
        column_registry,
        required=["customer_id", "order_date", "order_id", "revenue"],
    )

    # 입력 DataFrame 검증
    if df is None or df.empty:
        raise ValueError("분석할 데이터가 없습니다.")
    
    # Falg 컬럼 제외한 데이터 컬럼만 사용
    data = [
        col for col in df.columns
        if not col.startswith("is_")
    ]

    data_df = df[data]

    # customer_id가 결측(혹은 공백)인 row는 제외
    data_df = data_df[
        data_df["customer_id"].notna()
        & (data_df["customer_id"].str.strip() != "")
    ]

    # RFM 값 계산
    rfm_df = _calculate_rfm(data_df)

    # RFM 점수화
    rfm_df = _score_rfm(rfm_df)

    # 세그먼트 분류
    rfm_df = _assign_segment(rfm_df)

    # 세그먼트 요약 집계
    summary_df = _get_segment_summary(rfm_df)

    # 결과 반환
    return {
        "rfm_df" : rfm_df,
        "segment_summary" : summary_df
    }