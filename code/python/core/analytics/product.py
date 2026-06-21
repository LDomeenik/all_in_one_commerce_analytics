"""
product.py

상품 분석 모듈

기능:
    - 상품별 매출, 판매량, 평균 단가 집계
    - 매출/판매량 기준 Top N 상품 추출
    - 매출 집중도 계산
"""


import pandas as pd

from core.analytics.table_selector import get_dataframe_with_columns


# _get_product_summary: 상품별 요약 집계
def _get_product_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    상품별 총 매출, 판매량, 평균 단가, 주문 수를 집계합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
    
    Returns:
        pd.DataFrame: 상품별 요약
            - product_id (str): 상품 ID
            - product_name (str): 상품명
            - total_revenue (float): 총 매출 (item_revenue 합계)
            - total_quantity (int): 총 판매량 (quantity가 있는 경우)
            - avg_unit_price (float): 평균 단가 (unit_price가 있는 경우)
            - order_count (int): 상품이 포함된 주문 수
    
    Raises:
        없음
    """

    # groupby 기준 컬럼 결정
    group_cols = ["product_id", "product_name"] if "product_name" in df.columns else ["product_id"]

    # 집계 기준 딕셔너리 구성
    agg_dict = {
        "item_revenue" : "sum",
        "order_id" : "nunique"
    }

    # quantity, unit_price가 있으면 agg_dict에 추가
    if "quantity" in df.columns:
        agg_dict["quantity"] = "sum"
    if "unit_price" in df.columns:
        agg_dict["unit_price"] = "mean"
    
    # 집계
    summary = (
        df.groupby(group_cols)
        .agg(agg_dict)
        .reset_index()
        .rename(columns={
            "item_revenue" : "total_revenue",
            "order_id" : "order_count",
            "quantity" : "total_quantity",
            "unit_price" : "avg_unit_price"
        })
    )

    # 결과 반환
    return summary


# _get_top_products: 매출/판매량 기준 Top N 상품 추출
def _get_top_products(
        product_summary: pd.DataFrame,
        n: int = 10
) -> dict:
    """
    매출 및 판매량 기준 Top N 상품을 추출합니다.

    Args:
        product_summary (pd.DataFrame): 상품별 요약 DataFrame
        n (int): 추출할 상품 수 (기본값 10)
    
    Returns:
        dict:
            - top_revenue (pd.DataFrame): 매출 기준 Top N 상품
            - top_quantity (pd.DataFrame): 판매량 기준 Top N 상품 (quantity 있는 경우)
    
    Raises:
        없음
    """

    # 매출 기준 Top N
    top_revenue = (
        product_summary
        .sort_values("total_revenue", ascending=False)
        .head(n)
    )

    # 판매량 기준 Top N
    top_quantity = None
    if "total_quantity" in product_summary.columns:
        top_quantity = (
            product_summary
            .sort_values("total_quantity", ascending=False)
            .head(n)
        )
    
    # 결과 반환
    return {
        "top_revenue" : top_revenue,
        "top_quantity" : top_quantity
    }


# _get_concentration: 매출 집중도 계산
def _get_concentration(product_summary: pd.DataFrame) -> dict:
    """
    상위 N개 상품의 매출 집중도를 계산합니다.

    Args:
        product_summary (pd.DataFrame): 상품별 요약 DataFrame
    
    Returns:
        dict:
            - total_products (int): 전체 상품 수
            - total_revenue (float): 전체 매출 합계
            - top3_revenue_pct (float): 상위 3개 상품 매출 비율 (%)
            - top5_revenue_pct (float): 상위 5개 상품 매출 비율 (%)
            - top10_revenue_pct (float): 상위 10개 상품 매출 비율 (%)
    
    Raises:
        없음
    """

    # 전체 상품 수
    total_products = len(product_summary)

    # 전체 매출 합계
    total_revenue = product_summary["total_revenue"].sum()

    # 매출 기준 내림차순 정렬
    sorted_df = product_summary.sort_values("total_revenue", ascending=False)

    # 상위 N개 매출 비율 계산 내부 함수
    def _top_n_pct(n):
        if total_revenue == 0 or total_products < n:
            return None
        top_n_revenue = sorted_df.head(n)["total_revenue"].sum()
        return top_n_revenue / total_revenue * 100

    # 결과 반환
    return {
        "total_products" : total_products,
        "total_revenue" : total_revenue,
        "top3_revenue_pct" : _top_n_pct(3),
        "top5_revenue_pct" : _top_n_pct(5),
        "top10_revenue_pct" : _top_n_pct(10)
    }


# run_product: 상품 분석 실행
def run_product(tables: dict[str, pd.DataFrame], column_registry: dict[str, str]) -> dict:
    """
    상품 분석을 실행합니다.

    Args:
        tables (dict[str, pd.DataFrame]): 테이블 딕셔너리
        column_registry (dict[str, str]): {컬럼명: 테이블유형} 레지스트리
    
    Returns:
        dict: 상품 분석 결과
            - product_summary (pd.DataFrame): 상품별 요약
            - top_products (dict): 매출/판매량 기준 Top N 상품
            - concentration (dict): 매출 집중도
        
    Raises:
        ValueError: 입력 DataFrame이 비어 있는 경우
    """

    # 필요한 컬럼을 가진 테이블 자동 선택
    df = get_dataframe_with_columns(
        tables,
        column_registry,
        required=["product_id", "item_revenue", "order_id", "product_name", "quantity"],
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

    # 상품별 요약 집계
    product_summary = _get_product_summary(data_df)

    # Top N 상품 추출
    top_products = _get_top_products(product_summary)

    # 매출 집중도 계산
    concentration = _get_concentration(product_summary)

    # 결과 반환
    return {
        "product_summary" : product_summary,
        "top_products" : top_products,
        "concentration" : concentration
    }