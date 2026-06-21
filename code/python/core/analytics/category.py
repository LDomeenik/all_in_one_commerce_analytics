"""
category.py

카테고리 분석 모듈

기능:
    - 카테고리별 매출, 판매량, 상품 수, AOV, 매출 비율 집계
"""


import pandas as pd

from core.analytics.table_selector import get_dataframe_with_columns


# _get_category_summary: 카테고리별 요약 집계
def _get_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    카테고리별 총 매출, 판매량, 상품 수, AOV, 매출 비율을 집계합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
    
    Returns:
        pd.DataFrame: 카테고리별 요약
            - product_category (str): 카테고리명
            - total_revenue (float): 총 매출
            - revenue_pct (float): 전체 매출 대비 비율 (%)
            - total_quantity (int): 총 판매량 (quantity 있는 경우)
            - product_count (int): 카테고리 내 상품 수
            - order_count (int): 주문 수
            - aov (float): 평균 주문 금액
    
    Raises:
        없음
    """

    # 집계 기준 딕셔너리 구성
    agg_dict = {
        "item_revenue" : "sum",
        "order_id" : "nunique",
        "product_id" : "nunique"
    }

    if "quantity" in df.columns:
        agg_dict["quantity"] = "sum"
    
    # 집계
    summary = (
        df.groupby("product_category")
        .agg(agg_dict)
        .reset_index()
        .rename(columns={
            "item_revenue": "total_revenue",
            "order_id": "order_count",
            "product_id": "product_count",
            "quantity": "total_quantity"
        })
    )

    # AOV
    summary["aov"] = summary["total_revenue"] / summary["order_count"]

    # 매출 비율
    total_revenue = summary["total_revenue"].sum()
    summary["revenue_pct"] = summary["total_revenue"] / total_revenue * 100.0

    # 매출 기준 내림차순 정렬
    summary = summary.sort_values("total_revenue", ascending=False)

    return summary


# run_category: 카테고리 분석 실행
def run_category(tables: dict[str, pd.DataFrame], column_registry: dict[str, str]) -> dict:
    """
    카테고리 분석을 실행합니다.

    Args:
        tables (dict[str, pd.DataFrame]): 테이블 딕셔너리
        column_registry (dict[str, str]): {컬럼명: 테이블유형} 레지스트리
    
    Returns:
        dict: 카테고리 분석 결과
            - category_summary (pd.DataFrame): 카테고리별 요약
    
    Raises:
        ValueError: 입력 DataFrame이 비어 있는 경우
    """

    # 필요한 컬럼을 가진 테이블 자동 선택
    df = get_dataframe_with_columns(
        tables,
        column_registry,
        required=["product_category", "item_revenue", "order_id"],
        agg={"item_revenue":"sum"}
    )

    # 입력 DataFrame 검증
    if df is None or df.empty:
        raise ValueError("분석할 데이터가 없습니다.")
    
    # Flag 컬럼 제외한 데이터 컬럼만 사용
    data = [
        col for col in df.columns
        if not col.startswith("is_")
    ]

    data_df = df[data]

    # 카테고리별 요약 집계
    category_summary = _get_category_summary(data_df)

    # 결과 반환
    return {
        "category_summary": category_summary
    }