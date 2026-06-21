"""
validator.py

Staging DataFrame 의 데이터 정합성을 검증하고 Flag 를 생성하는 모듈

기능:
    - 필수 컬럼 결측 여부 Flag 생성
    - 날짜 정합성 검증 Flag 생성
    - 금액 정합성 검증 Flag 생성
    - 수량 정합성 검증 Flag 생성
    - 중복 데이터 검증 Flag 생성
    - Derived 컬럼 생성 (delivery_days, is_delayed)
    - 전체 정합성 검증 실행
"""


import pandas as pd

from core.loader.config_loader import get_columns_required_for


# _add_missing_flags: 필수 컬럼 결측 여부 Flag 생성
def _add_missing_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    분석 모듈별 필수 컬럼의 결측 여부 Flag를 생성합니다.
    컬럼이 존재하는 경우에만 Flag를 생성합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame

    Returns:
        pd.DataFrame: 결측 Flag가 추가된 DataFrame

    Raises:
        없음
    """

    result_df = df.copy()

    # 전체 분석 모듈의 필수 컬럼 수집
    modules = ["eda", "kpi", "cohort", "rfm", "product", "category", "delivery"]
    required_columns = set()

    for module in modules:
        required_columns.update(get_columns_required_for(module))

    # 컬럼이 존재하는 경우에만 결측 Flag 생성
    for column in required_columns:
        if column in result_df.columns:
            result_df[f"is_missing_{column}"] = result_df[column].isna()
        # 컬럼이 없으면 flag 생성 안 함

    return result_df


# _add_date_validation_flags: 날짜 정합성 Flag 생성
def _add_date_validation_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    날짜 컬럼 간 순서 정합성 Flag 를 생성합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame

    Returns:
        pd.DataFrame: 날짜 정합성 Flag 가 추가된 DataFrame

    Raises:
        없음
    """

    result_df = df.copy()

    # 주문일 > 배송완료일 여부 검증
    if (
        "order_date" in result_df.columns
        and "delivered_date" in result_df.columns
    ):
        result_df["is_invalid_delivery_flow"] = (
            result_df["order_date"].notna()
            & result_df["delivered_date"].notna()
            & (result_df["order_date"] > result_df["delivered_date"])
        )

    # 주문일 > 출고일 여부 검증
    if (
        "order_date" in result_df.columns
        and "shipped_date" in result_df.columns
    ):
        result_df["is_invalid_shipping_flow"] = (
            result_df["order_date"].notna()
            & result_df["shipped_date"].notna()
            & (result_df["order_date"] > result_df["shipped_date"])
        )

    # 출고일 > 배송완료일 여부 검증
    if (
        "shipped_date" in result_df.columns
        and "delivered_date" in result_df.columns
    ):
        result_df["is_invalid_shipment_flow"] = (
            result_df["shipped_date"].notna()
            & result_df["delivered_date"].notna()
            & (result_df["shipped_date"] > result_df["delivered_date"])
        )

    return result_df


# _add_amount_validation_flags: 금액 정합성 Flag 생성
def _add_amount_validation_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    금액 컬럼의 정합성 Flag 를 생성합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame

    Returns:
        pd.DataFrame: 금액 정합성 Flag 가 추가된 DataFrame

    Raises:
        없음
    """

    result_df = df.copy()

    # revenue 음수 여부 검증
    if "revenue" in result_df.columns:
        result_df["is_negative_revenue"] = (
            result_df["revenue"].notna()
            & (result_df["revenue"] < 0)
        )

    # unit_price 음수 여부 검증
    if "unit_price" in result_df.columns:
        result_df["is_negative_unit_price"] = (
            result_df["unit_price"].notna()
            & (result_df["unit_price"] < 0)
        )

    # shipping_fee 음수 여부 검증
    if "shipping_fee" in result_df.columns:
        result_df["is_negative_shipping_fee"] = (
            result_df["shipping_fee"].notna()
            & (result_df["shipping_fee"] < 0)
        )

    return result_df


# _add_quantity_validation_flags: 수량 정합성 Flag 생성
def _add_quantity_validation_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    수량 컬럼의 정합성 Flag 를 생성합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame

    Returns:
        pd.DataFrame: 수량 정합성 Flag 가 추가된 DataFrame

    Raises:
        없음
    """

    result_df = df.copy()

    # quantity 0 이하 여부 검증
    if "quantity" in result_df.columns:
        result_df["is_invalid_quantity"] = (
            result_df["quantity"].notna()
            & (result_df["quantity"] <= 0)
        )

    return result_df


# _add_duplicate_flags: 중복 데이터 Flag 생성
def _add_duplicate_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    중복 데이터 여부 Flag 를 생성합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame

    Returns:
        pd.DataFrame: 중복 Flag 가 추가된 DataFrame

    Raises:
        없음
    """

    result_df = df.copy()

    # order_id 중복 여부 검증
    # order_item_id 가 있는 경우 복합 키 기준으로 검증
    if "order_id" in result_df.columns:
        if "order_item_id" in result_df.columns:
            result_df["is_duplicated_order"] = result_df.duplicated(
                subset=["order_id", "order_item_id"],
                keep="first"
            )
        else:
            result_df["is_duplicated_order"] = result_df.duplicated(
                subset=["order_id"],
                keep="first"
            )

    return result_df


# _add_derived_columns: Derived 컬럼 생성
def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    원본 데이터에서 파생되는 Derived 컬럼을 생성합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame

    Returns:
        pd.DataFrame: Derived 컬럼이 추가된 DataFrame

    Raises:
        없음
    """

    result_df = df.copy()

    # delivery_days 생성
    # shipped_date 와 delivered_date 가 모두 있는 경우 생성
    if (
        "shipped_date" in result_df.columns
        and "delivered_date" in result_df.columns
        and "delivery_days" not in result_df.columns
    ):
        result_df["delivery_days"] = (
            result_df["delivered_date"] - result_df["shipped_date"]
        ).dt.days

    # is_delayed 생성
    # delivered_date 와 estimated_delivery_date 가 모두 있는 경우 생성
    if (
        "delivered_date" in result_df.columns
        and "estimated_delivery_date" in result_df.columns
        and "is_delayed" not in result_df.columns
    ):
        result_df["is_delayed"] = (
            result_df["delivered_date"].notna()
            & result_df["estimated_delivery_date"].notna()
            & (result_df["delivered_date"] > result_df["estimated_delivery_date"])
        )

    # item_revenue 생성
    if (
        "item_revenue" not in result_df.columns
        and "unit_price" in result_df.columns
        and "quantity" in result_df.columns
    ):
        result_df["item_revenue"] = (
            result_df["unit_price"] * result_df["quantity"]
        )
    
    # revenue 생성
    if "revenue" not in result_df.columns:
        if (
            "item_revenue" in result_df.columns
            and "shipping_fee" in result_df.columns
        ):
            result_df["revenue"] = (
                result_df["item_revenue"] + result_df["shipping_fee"]
            )
        elif "item_revenue" in result_df.columns:
            result_df["revenue"] = result_df["item_revenue"]

    return result_df


# validate_dataframe: 전체 정합성 검증 실행
def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Staging DataFrame 에 전체 정합성 검증을 실행합니다.

    Args:
        df (pd.DataFrame): Staging DataFrame

    Returns:
        pd.DataFrame: 정합성 검증 Flag 와 Derived 컬럼이 추가된 DataFrame

    Raises:
        없음
    """

    result_df = _add_derived_columns(df)
    result_df = _add_missing_flags(result_df)
    result_df = _add_date_validation_flags(result_df)
    result_df = _add_amount_validation_flags(result_df)
    result_df = _add_quantity_validation_flags(result_df)
    result_df = _add_duplicate_flags(result_df)

    return result_df