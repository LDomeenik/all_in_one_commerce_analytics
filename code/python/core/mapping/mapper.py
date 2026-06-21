"""
mapper.py

Alias Dictionary와 Rule-Based 매핑을 통합하여 최종 컬럼 매핑 결과를 생성하는 모듈

기능:
    - Alias + Rule-Based 통합 매핑 실행
    - 매핑 우선순위 적용 (Alias → Rule-Based → 미매핑)
    - confirmed 필드 포함 최종 매핑 결과 생성
    - 사용자 확정 결과 반영
    - 확정된 매핑 결과 적용 및 미매핑 컬럼 추출
    - 중복 매핑 탐지
"""


import pandas as pd

from core.mapping.normalizer import normalize_columns
from core.mapping.alias_mapper import map_column_by_alias
from core.mapping.rule_mapper import map_column_by_rule


# map_columns: 통합 컬럼 매핑 실행
def map_columns(columns: list) -> dict:
    """
    전체 컬럼 목록에 대해 Alias → Rule-Based 통합 매핑을 수행합니다.

    Args:
        columns (list): 원본 컬럼명 리스트
    
    Returns:
        dict: 전체 컬럼 통합 매핑 결과
            {
                원본 컬럼명: {
                    "normalized_column": 정규화된 컬럼명,
                    "mapped_to": 표준 컬럼명 또는 None,
                    "confidence": 신뢰도,
                    "source": 매핑 근거,
                    "confirmed": 사용자 확정 여부
                }
            }
    
    Raises:
        없음
    """

    # 컬럼 정규화
    normalized_columns = normalize_columns(columns)

    # 매핑 결과 저장용 딕셔너리 생성
    mapping_result = {}

    for source_column, normalized_column in normalized_columns.items():
        # Alias 매핑 시도
        alias_result = map_column_by_alias(normalized_column)

        if alias_result["mapped_to"] is not None:
            final_result = alias_result
        else:
            # Rule-Based 매핑 시도
            final_result = map_column_by_rule(normalized_column)
        
        # confirmed 필드 추가
        mapping_result[source_column] = {
            "normalized_column": normalized_column,
            "mapped_to": final_result["mapped_to"],
            "confidence": final_result["confidence"],
            "source": final_result["source"],
            "confirmed": False
        }
    
    return mapping_result


# confirm_mapping: 사용자 확정 결과를 매핑 결과에 반영
def confirm_mapping(
        mapping_result: dict,
        user_selections: dict
) -> dict:
    """
    사용자가 선택한 매핑 결과를 최종 매핑 결과에 반영합니다.

    Args:
        mapping_result (dict): 자동 매핑 결과
        user_selections (dict): 사용자가 선택한 매핑 결과
            {원본 컬럼명: 사용자가 선택한 표준 컬럼명 또는 None}
    
    Returns:
        dict: confirmed가 반영된 최종 매핑 결과
    
    Raises:
        없음
    """

    # 확정 매핑 결과 저장용 딕셔너리 생성
    confirmed_mapping = {}

    for source_column, info in mapping_result.items():
        # 사용자 선택값 추출
        selected = user_selections.get(source_column, info["mapped_to"])

        confirmed_mapping[source_column] = {
            **info,
            "mapped_to": selected,
            "confirmed": selected is not None
        }
    
    return confirmed_mapping


# build_rename_dict: 확정 매핑 결과에서 rename 딕셔너리 생성
def build_rename_dict(confirmed_mapping: dict) -> dict:
    """
    확정된 매핑 결과에서 DataFrame rename용 딕셔너리를 생성합니다.

    Args:
        confirmed_mapping (dict): Human Review를 거친 최종 매핑 결과
    
    Returns:
        dict: {원본 컬럼명: 표준 컬럼명} 딕셔너리
    
    Raises:
        없음
    """

    return {
        source_column: info["mapped_to"] 
        for source_column, info in confirmed_mapping.items()
        if info["mapped_to"] is not None
    }


# extract_unmapped_columns: 미매핑 컬럼 목록 추출
def extract_unmapped_columns(confirmed_mapping: dict) -> list:
    """
    확정된 매핑 결과에서 미매핑 컬럼 목록을 추출합니다.

    Args:
        confirmed_mapping (dict): Human Review를 거친 최종 매핑 결과
    
    Returns:
        list: 표준 컬럼으로 매핑되지 않은 원본 컬럼 목록
    
    Raises:
        없음
    """

    return [
        source_column
        for source_column, info in confirmed_mapping.items()
        if info["mapped_to"] is None
    ]


# detect_duplicate_mappings: 중복 매핑 탐지
def detect_duplicate_mappings(rename_dict: dict) -> dict:
    """
    여러 원본 컬럼이 동일한 표준 컬럼으로 매핑된 경우를 탐지합니다.

    Args:
        rename_dict (dict): {원본 컬럼명: 표준 컬럼명} 딕셔너리
    
    Returns:
        dict: 중복 매핑 정보
            {표준 컬럼명: [중복된 원본 컬럼명 목록]}
            중복이 없으면 빈 딕셔너리 반환
    
    Raises:
        없음
    """

    # 표준 컬럼 → 원본 컬럼 역방향 추적
    mapped_targets = {}
    duplicate_mappings = {}

    for source_column, standard_column in rename_dict.items():
        if standard_column in mapped_targets:
            if standard_column not in duplicate_mappings:
                duplicate_mappings[standard_column] = [mapped_targets[standard_column]]
            duplicate_mappings[standard_column].append(source_column)
        
        else:
            mapped_targets[standard_column] = source_column
    
    return duplicate_mappings


# apply_mapping: 확정 매핑 결과를 DataFrame에 적용
def apply_mapping(
        df: pd.DataFrame,
        confirmed_mapping: dict
) -> tuple[pd.DataFrame, dict, list, dict]:
    """
    확정된 매핑 결과를 DataFrame에 적용하여 Staging DataFrame을 생성합니다.

    Args:
        df (pd.DataFrame): 원본 DataFrame
        confirmed_mapping (dict): Human Review를 거친 최종 매핑 결과
    
    Returns:
        tuple:
            - pd.DataFrame: 표준 컬럼명으로 변환된 Staging DataFrame
            - dict: 적용된 rename 딕셔너리
            - list: 미매핑 컬럼 목록
    
    Raises:
        ValueError: 확정된 매핑 결과가 비어 있는 경우
        ValueError: 중복 매핑이 존재하는 경우
    """

    if not confirmed_mapping:
        raise ValueError("확정된 매핑 결과가 없습니다.")
    
    # rename 딕셔너리 및 미매핑 컬럼 추출
    rename_dict = build_rename_dict(confirmed_mapping)
    unmapped_columns = extract_unmapped_columns(confirmed_mapping)

    # 중복 매핑 탐지
    duplicate_mappings = detect_duplicate_mappings(rename_dict)

    if duplicate_mappings:
        raise ValueError(f"중복 매핑이 존재합니다. 확인 후 다시 시도해주세요: {duplicate_mappings}")

    # Staging DataFrame 생성
    staging_df = df.copy()
    staging_df = staging_df.drop(columns=unmapped_columns, errors="ignore")
    staging_df = staging_df.rename(columns=rename_dict)
    existing_standard_cols = [
        col for col in rename_dict.values()
        if col in staging_df.columns
    ]
    staging_df = staging_df[existing_standard_cols]

    return staging_df, rename_dict, unmapped_columns