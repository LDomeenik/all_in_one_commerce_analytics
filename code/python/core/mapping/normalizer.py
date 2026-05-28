"""
normalizer.py

원본 컬럼명을 표준 형태로 정규화하는 모듈

기능:
    - 앞뒤 공백 제거
    - CamelCase를 snake_case로 변환
    - 소문자 변환
    - 특수문자를 언더스코어로 변환
    - 중복 언더스코어 제거
    - 한글 컬럼명 공백 제거
    - 전체 컬럼 목록 정규화
"""


import re


# normalize_column_name: 단일 컬럼명 정규화
def normalize_column_name(column_name: str) -> str:
    """
    원본 컬럼명을 비교 가능한 표준 형태로 정규화합니다.
    
    Args:
        column_name (str): 원본 컬럼명
    
    Returns:
        str: 정규화된 컬럼명
    
    Raises:
        TypeError: column_name이 문자열이 아닌 경우
    """

    # column_name이 문자열이 아닌 경우 에러
    if not isinstance(column_name, str):
        raise TypeError(f"컬럼명은 문자열이어야 합니다. 입력값: {type(column_name)}")
    
    # 앞뒤 공백 제거
    normalized = column_name.strip()

    # CamelCase → snake_case 변환
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)

    # 소문자 변환
    normalized = normalized.lower()

    # 한글이 포함된 경우 공백 및 특수문자 제거
    if re.search(r"[가-힣]", normalized):
        normalized = re.sub(r"[\s\-_.]+", "", normalized)
        return normalized
    
    # 특수문자 → 언더스코어로 변환
    normalized = re.sub(r"[\s\-.]+", "_", normalized)

    # 중복 언더스코어 제거
    normalized = re.sub(r"_+", "_", normalized)

    # 앞뒤 언더스코어 제거
    normalized = normalized.strip("_")

    return normalized


# normalize_columns: 컬럼 목록 전체 정규화
def normalize_columns(columns: list) -> dict:
    """
    컬럼 목록 전체를 정규화하여 원본 컬럼명과 정규화된 컬럼명의 매핑 딕셔너리를 반환합니다.

    Args:
        columns (list): 원본 컬럼명 리스트
    
    Returns:
        dict: {원본 컬럼명: 정규화된 컬럼명} 딕셔너리
    
    Raises:
        없음
    """

    return {
        column: normalize_column_name(column)
        for column in columns
    }