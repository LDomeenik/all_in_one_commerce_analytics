"""
alias_mapper.py

Alias Dictionary 기반으로 컬럼을 표준 컬럼에 매핑하는 모듈

기능:
    - Alias Dictionary 역방향 조회 구조 생성
    - 단일 컬럼 Alias 매핑
    - 전체 컬럼 목록 Alias 매핑
"""


from core.loader.config_loader import load_alias_dictionary
from core.mapping.normalizer import normalize_column_name


# _build_alias_lookup: Alias Dictionary를 역방향 조회 구조로 변환
def _build_alias_lookup() -> dict:
    """
    Alias Dictionary를 alias 기준 역방향 조회 구조로 변환하는 내장 함수입니다.

    Args:
        없음
    
    Returns:
        dict: {정규화된 alias: 표준 컬럼명} 딕셔너리
    
    Raises:
        없음
    """

    # alias_dictionary 불러오기
    alias_dict = load_alias_dictionary()

    # 역방향 구조로 저장할 딕셔너리 생성
    alias_lookup = {}

    # 역방향 구조로 저장
    for standard_column, aliases in alias_dict.items():
        for alias in aliases:
            # alias 정규화
            normalized_alias = normalize_column_name(alias)
            alias_lookup[normalized_alias] = standard_column
    
    return alias_lookup


# map_column_by_alias: 단일 컬럼 Alias 매핑
def map_column_by_alias(normalized_column: str) -> dict:
    """
    정규화된 컬럼명을 Alias Dictionary 기준으로 표준 컬럼에 매핑합니다.

    Args:
        normalized_column (str): 정규화된 컬럼명
    
    Returns:
        dict: 매핑 결과
            - mapped_to (str | None): 매핑된 표준 컬럼명
            - confidence (float): 매핑 신뢰도
            - source (list): 매핑 근거
    
    Raises:
        없음
    """

    # alias_dictionary 불러오기
    alias_lookup = _build_alias_lookup()

    # dict 매핑
    if normalized_column in alias_lookup:
        return {
            "mapped_to": alias_lookup[normalized_column],
            "confidence": 1.0,
            "source": ["alias"]
        }
    
    # 결과 반환
    return {
        "mapped_to": None,
        "confidence": 0.0,
        "source": []
    }