"""
table_selector.py

컬럼 기반 테이블 선택 및 JOIN 유틸리티 모듈

기능:
    - 전처리 완료 테이블에서 컬럼 레지스트리 생성
    - 필요한 컬럼을 가진 테이블 자동 선택
    - 필요 시 테이블 간 JOIN 및 집계 처리
"""


import pandas as pd


# JOIN 키 후보 컬럼 목록
JOIN_KEY_CANDIDATES = [
    "order_id",
    "customer_id",
    "product_id",
    "seller_id",
    "order_item_id"
]

# 기준 테이블 우선순위 (JOIN 시 left 테이블 결정 기준)
TABLE_PRIORITY = [
    "order",
    "customer",
    "order_item",
    "product",
    "payment",
    "delivery"
]


# _find_join_key: 두 DataFrame의 공통 JOIN 키 탐지
def _find_join_key(df1: pd.DataFrame, df2: pd.DataFrame) -> str | None:
    """
    두 DataFrame에 공통으로 존재하는 JOIN 키 컬럼을 탐지합니다.

    Args:
        df1 (pd.DataFrame): 첫 번째 DataFrame
        df2 (pd.DataFrame): 두 번째 DataFrame

    Returns:
        str | None: 공통 JOIN 키 컬럼명, 없으면 None

    Raises:
        없음
    """

    # JOIN 키 후보 순서대로 두 테이블에 공통으로 존재하는 컬럼 탐지
    for key in JOIN_KEY_CANDIDATES:
        if key in df1.columns and key in df2.columns:
            return key

    return None


# build_column_registry: 컬럼 레지스트리 생성
def build_column_registry(
    preprocessed_tables: dict[str, pd.DataFrame]
) -> dict[str, str]:
    """
    전처리 완료 테이블에서 {컬럼명: 테이블유형} 레지스트리를 생성합니다.
    is_ 로 시작하는 flag 컬럼은 제외합니다.

    Args:
        preprocessed_tables (dict[str, pd.DataFrame]): 전처리 완료 테이블 딕셔너리

    Returns:
        dict[str, str]: {컬럼명: 테이블유형} 딕셔너리
            예: {"order_id": "order", "item_revenue": "order_item"}

    Raises:
        없음
    """

    registry = {}

    # 각 테이블 순회하며 컬럼명 → 테이블 유형 저장
    for table_type, df in preprocessed_tables.items():

        # flag 컬럼 제외하고 컬럼명 → 테이블 유형 저장
        for col in df.columns:
            if not col.startswith("is_"):
                registry[col] = table_type

    return registry


# get_dataframe_with_columns: 컬럼 기반 테이블 자동 선택
def get_dataframe_with_columns(
    tables: dict[str, pd.DataFrame],
    column_registry: dict[str, str],
    required: list[str],
    agg: dict[str, str] = None,
    join_how: str = "left"
) -> pd.DataFrame | None:
    """
    필요한 컬럼을 가진 테이블을 자동으로 선택하고
    필요 시 JOIN 및 집계를 수행하여 반환합니다.

    Args:
        tables (dict[str, pd.DataFrame]): 전처리 완료 테이블 딕셔너리
        column_registry (dict[str, str]): {컬럼명: 테이블유형} 레지스트리
        required (list[str]): 필요한 컬럼 목록
        agg (dict[str, str]): 집계 방식 {컬럼명: 집계함수}
            예: {"item_revenue": "sum", "shipping_fee": "sum"}
        join_how (str): JOIN 방식 (기본값: "left")

    Returns:
        pd.DataFrame | None: 선택된 DataFrame, 필요한 컬럼이 없으면 None

    Raises:
        없음
    """

    # required 컬럼이 어느 테이블에 있는지 확인
    tables_needed = set()

    for col in required:
        if col in column_registry:
            tables_needed.add(column_registry[col])

    # 필요한 컬럼이 하나도 레지스트리에 없으면 None 반환
    if not tables_needed:
        return None

    # 단일 테이블이면 바로 반환
    if len(tables_needed) == 1:
        table_type = list(tables_needed)[0]
        df = tables[table_type]

        # required 중 실제로 존재하는 컬럼만 선택
        existing_cols = [col for col in required if col in df.columns]
        return df[existing_cols]

    # 여러 테이블이 필요하면 JOIN
    # TABLE_PRIORITY 기준으로 기준 테이블(left) 결정
    base_table = next(
        (t for t in TABLE_PRIORITY if t in tables_needed),
        list(tables_needed)[0]
    )

    result_df = tables[base_table].copy()

    # 나머지 테이블들을 순서대로 JOIN
    for table_type in tables_needed:
        if table_type == base_table:
            continue

        other_df = tables[table_type].copy()

        # 공통 JOIN 키 탐지
        join_key = _find_join_key(result_df, other_df)

        if join_key is None:
            continue

        # agg가 있으면 JOIN 전에 집계 먼저 실행 (행 뻥튀기 방지)
        if agg:
            agg_cols = {k: v for k, v in agg.items() if k in other_df.columns}
            if agg_cols:
                other_df = other_df.groupby(join_key).agg(agg_cols).reset_index()

        # JOIN 실행
        result_df = result_df.merge(other_df, on=join_key, how=join_how)

    # required 중 실제로 존재하는 컬럼만 선택해서 반환
    existing_cols = [col for col in required if col in result_df.columns]
    return result_df[existing_cols]