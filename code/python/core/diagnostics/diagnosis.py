"""
diagnosis.py

분석 모듈별 실행 가능 여부를 진단하는 모듈

기능:
    - 분석 모듈별 필수 컬럼 존재 여부 확인
    - 필수 컬럼 결측 비율 계산
    - 선택 컬럼 존재 여부 확인
    - 전체 분석 모듈 진단 실행
"""


import pandas as pd

from core.loader.config_loader import (
    get_columns_required_for,
    load_standard_columns
)


# 분석 모듈 목록 지정
ANALYSIS_MODULES = {
    "eda" : "EDA",
    "kpi" : "KPI 분석",
    "cohort" : "코호트 분석",
    "rfm" : "RFM / 재구매 분석",
    "product" : "상품 분석",
    "category" : "카테고리 분석",
    "delivery" : "배송 / 운영 분석"
}


# _calculate_null_rate: 컬럼별 결측 비율 계산
def _calculate_null_rate(df: pd.DataFrame, columns: list) -> dict:
    """
    존재하는 컬럼의 결측 비율을 계산합니다.

    Args:
        df (pd.DataFrame): 전처리 완료 DataFrame
        columns (list): 결측 비율을 계산할 컬럼 목록
    
    Returns:
        dict: {컬럼명: 결측 비율(%)} 딕셔너리
    
    Raises:
        없음
    """

    null_rate = {}

    for column in columns:
        if column in df.columns:
            rate = round(df[column].isna().mean() * 100, 1)
            null_rate[column] = rate
    
    return null_rate


# _get_optional_columns: 선택 컬럼 목록 조회
def _get_optional_columns(module: str) -> list:
    """
    분석 모듈의 선택 컬럼 목록을 반환합니다.
    standard_columns.json에서 required_for에 해당 모듈이 없는 컬럼 중 category가 관련된 컬럼을 선택 컬럼으로 반환합니다.

    Args:
        module (str): 분석 모듈 키
    
    Returns:
        list: 선택 컬럼 목록
    
    Raises:
        없음
    """

    standard_columns = load_standard_columns()
    required_columns = get_columns_required_for(module)

    # 모듈과 관련된 카테고리 정의
    module_category_map = {
        "eda" : ["core", "customer", "product", "payment", "logistics"],
        "kpi" : ["core", "product", "logistics"],
        "cohort" : ["core", "customer"],
        "rfm" : ["core", "customer", "product"],
        "product" : ["product"],
        "category" : ["product"],
        "delivery" : ["logistics"]
    }

    related_categories = module_category_map.get(module, [])

    optional_columns = [
        col for col, info in standard_columns.items()
        if col not in required_columns
        and info["category"] in related_categories
        and info.get("category") != "derived"
    ]

    return optional_columns


# _diagnose_module: 단일 분석 모듈 진단
def _diagnose_module(df: pd.DataFrame, module: str) -> dict:
    """
    단일 분석 모듈의 실행 가능 여부를 진단합니다.

    Args:
        df (pd.DataFrame): 파생 컬럼이 추가된 DataFrame
        module (str): 분석 모듈 키
    
    Returns:
        dict: 진단 결과
            - available (bool): 실행 가능 여부
            - status (str): 실행 상태
            - missing_columns (list): 없는 필수 컬럼 목록
            - optional_missing (list): 없는 선택 컬럼 목록
            - null_rate (dict): 필수 컬럼별 결측 비율
    
    Raises:
        없음
    """

    required_columns = get_columns_required_for(module)
    optional_columns = _get_optional_columns(module)

    # 필수 컬럼 존재 여부 확인
    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    # 선택 컬럼 존재 여부 확인
    optional_missing = [
        col for col in optional_columns
        if col not in df.columns
    ]

    # 필수 컬럼 결측 비율 계산
    existing_required = [
        col for col in required_columns
        if col in df.columns
    ]

    null_rate = _calculate_null_rate(df, existing_required)

    # 실행 가능 여부 판단
    available = len(missing_columns) == 0

    return {
        "available": available,
        "status": "실행 가능" if available else "실행 불가",
        "missing_columns": missing_columns,
        "optional_missing": optional_missing,
        "null_rate": null_rate
    }


# diagnose: 전체 분석 모듈 진단 실행
def diagnose(tables: dict) -> dict:
    """
    전처리 완료 DataFrame을 기반으로 전체 분석 모듈의 실행 가능 여부를 진단합니다.

    Args:
        tables (dict[str, pd.DataFrame]): 전처리 완료 테이블 딕셔너리
    
    Returns:
        dict: 전체 분석 모듈 진단 결과
            {
                모듈 키: {
                    "available": bool,
                    "status": str,
                    "missing_columns": list,
                    "optional_missing": list,
                    "null_rate": dict
                }
            }
    
    Raises:
        ValueError: 입력 tables가 비어 있는 경우
    """

    if not tables:
        raise ValueError("진단할 데이터가 없습니다.")
    
    # 모든 테이블에 존재하는 컬럼 목록 합집합
    all_columns = set()
    for df in tables.values():
        all_columns.update(
            col for col in df.columns
            if not col.startswith("is_")
        )

    # 빈 df에 컬럼만 설정해서 _diagnose_module에 전달
    dummy_df = pd.DataFrame(columns=list(all_columns))

    diagnosis_result = {}
    for module in ANALYSIS_MODULES.keys():
        diagnosis_result[module] = _diagnose_module(dummy_df, module)

    return diagnosis_result
