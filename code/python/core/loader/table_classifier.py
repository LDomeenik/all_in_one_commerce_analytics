"""
table_classifier.py

업로드된 파일의 테이블 유형을 추론하고 분류하는 모듈

기능:
    - DataFrame 컬럼 기반 테이블 유형 자동 추론
    - 다중 파일을 {테이블유형: DataFrame} 구조로 분류
"""


import pandas as pd

from core.mapping.normalizer import normalize_columns


# 테이블 유형별 컬럼 규칙 정의
# required: 반드시 존재해야 해당 유형으로 분류 가능한 컬럼
# optional: 존재할수록 점수가 높아지는 컬럼
TABLE_RULES = {
    "order": {
        "required": ["order_id"],
        "optional": ["order_date", "revenue", "order_status", "customer_id"]
    },
    "order_item": {
        "required": ["order_id", "product_id"],
        "optional": ["quantity", "unit_price", "item_revenue", "discount_amount"]
    },
    "customer": {
        "required": ["customer_id"],
        "optional": ["customer_name", "customer_city", "customer_state", "signup_date"]
    },
    "product": {
        "required": ["product_id"],
        "optional": ["product_name", "product_category", "brand_name", "unit_price"]
    },
    "payment": {
        "required": ["payment_method"],
        "optional": ["payment_amount", "payment_date", "payment_installments"]
    },
    "delivery": {
        "required": ["shipped_date"],
        "optional": ["delivered_date", "estimated_delivery_date", "delivery_days", "logistics_id"]
    },
    "event": {
        "required": ["event_name", "event_time"],
        "optional": ["session_id", "customer_id", "page_url", "event_value"]
    },
    "experiment": {
        "required": ["experiment_id", "variant", "conversion"],
        "optional": ["customer_id", "conversion_value"]
    }
}


# _normalize_columns: DataFrame 컬럼명 정규화
def _normalize_columns(df: pd.DataFrame) -> set[str]:
    """
    DataFrame의 컬럼명을 정규화하여 set으로 반환합니다.

    Args:
        df (pd.DataFrame): 정규화할 DataFrame

    Returns:
        set[str]: 정규화된 컬럼명 set

    Raises:
        없음
    """

    # 컬럼 목록 전체 정규화 후 정규화된 이름(값)만 set으로 반환
    # normalize_columns는 {원본명: 정규화명} 딕셔너리를 반환하므로 .values()로 값만 추출
    return set(normalize_columns(df.columns).values())


# infer_table_type: 단일 DataFrame 테이블 유형 추론
def infer_table_type(df: pd.DataFrame) -> str:
    """
    DataFrame의 컬럼을 분석하여 테이블 유형을 추론합니다.

    점수 계산 방식:
        - required 컬럼 중 하나라도 없으면 0점 (탈락)
        - required 모두 존재하면 기본 2점
        - optional 컬럼 매칭 1개당 1점 추가
        - 가장 높은 점수의 유형 반환
        - 점수가 0이면 "unknown" 반환

    Args:
        df (pd.DataFrame): 유형을 추론할 DataFrame

    Returns:
        str: 추론된 테이블 유형
            "order" / "order_item" / "customer" / "product"
            "payment" / "delivery" / "event" / "experiment" / "unknown"

    Raises:
        없음
    """

    # 컬럼명 정규화 (원본 컬럼명을 표준 형태로 변환)
    normalized_cols = _normalize_columns(df)

    # 가장 높은 점수의 테이블 유형 추적
    best_type = "unknown"
    best_score = 0

    for table_type, rules in TABLE_RULES.items():
        # required 컬럼이 모두 존재하는 경우에만 점수 계산
        if set(rules["required"]).issubset(normalized_cols):
            # required 통과 시 기본 2점 + optional 매칭 개수만큼 추가
            score = len(rules["required"]) * 2 + len(set(rules["optional"]) & normalized_cols)

            # 현재까지 가장 높은 점수면 갱신
            if score > best_score:
                best_score = score
                best_type = table_type

    return best_type


# classify_tables: 다중 파일을 테이블 유형별로 분류
def classify_tables(files_dict: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    여러 파일을 테이블 유형별로 분류하여 {테이블유형: DataFrame}으로 반환합니다.
    단일 파일인 경우 "order"로 처리합니다.

    Args:
        files_dict (dict[str, pd.DataFrame]): {파일명: DataFrame}

    Returns:
        dict[str, pd.DataFrame]: {테이블유형: DataFrame}

    Raises:
        없음
    """

    result = {}

    # 단일 파일인 경우 테이블 유형 추론 없이 "order"로 처리
    if len(files_dict) == 1:
        result["order"] = list(files_dict.values())[0]

    # 다중 파일인 경우 각 파일의 테이블 유형을 추론하여 분류
    elif len(files_dict) >= 2:
        for _, df in files_dict.items():
            # 컬럼 기반으로 테이블 유형 추론 후 딕셔너리에 저장
            table_type = infer_table_type(df)
            result[table_type] = df

    return result