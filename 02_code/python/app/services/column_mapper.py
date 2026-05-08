"""
column_mapper.py

업로드 데이터의 컬럼을 표준 컬럼으로 매핑하기 위한 모듈

기능:
    - 원본 컬럼명 정규화
    - Alias Dictionary JSON 로드
    - Alias Dictionary 기반 컬럼 매핑
    - 원본 컬럼별 매핑 결과 생성
"""


import re
import json
from pathlib import Path


# normalize_column_name: 원본 컬럼명을 비교 가능한 표준 형태로 정규화
def normalize_column_name(column_name: str) -> str:
    """
    원본 컬럼명 정규화

    Args:
        column_name (str): 원본 컬럼명
    
    Returns:
        str: 정규화된 컬럼명
    
    Raises:
        TypeError: column_name이 문자열이 아닌 경우 발생
    """

    # 컬럼명이 문자열이 아닌 경우 TypeError
    if not isinstance(column_name, str):
        raise TypeError("컬럼명은 문자열이어야 합니다.")
    
    # 앞뒤 공백 제거
    normalized = column_name.strip()

    # CamelCase -> snake_case
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)

    # 소문자 변환
    normalized = normalized.lower()

    # 공백, 하이픈, 점 등을 언더스코어로 변환
    normalized = re.sub(r"[\s\-.]+", "_", normalized)

    # 한글 컬럼의 언더스코어 제거 예외 처리
    if re.search(r"[가-힣]", normalized):
        normalized = normalized.replace("_", "")
    
    # 중복 언더스코어 정리
    normalized = re.sub(r"_+", "_", normalized)

    # 앞뒤 언더스코어 제거
    normalized = normalized.strip("_")

    return normalized


# normalize_columns: DataFrame 컬럼 목록을 정규화 딕셔너리로 변환
def normalize_columns(columns: list) -> dict:
    """
    컬럼 목록을 정규화된 컬럼명 딕셔너리로 변환

    Args:
        columns (list): 원본 컬럼명 리스트
    
    Returns:
        dict: 원본 컬럼명과 정규화 컬럼명을 담은 딕셔너리
    
    Raises:
        없음
    """

    return {
        column: normalize_column_name(column)
        for column in columns
    }


# load_alias_dictionary: JSON 파일에서 Alias Dictionary를 로드
def load_alias_dictionary() -> dict:
    """
    JSON 파일에서 Alias Dictionary를 로드

    Args:
        없음
    
    Returns:
        dict: 표준 컬럼별 alias 목록
    
    Raises:
        FileNotFoundError: Alias Dictionary JSON 파일이 존재하지 않는 경우 발생
        json.JSONDecodeError: Alias Dictionary JSON 파일 형식이 올바르지 않은 경우 발생
    """

    # 현재 파일 기준 json 경로 생성
    alias_path = (
        Path(__file__)
        .resolve()
        .parents[2]
        /"config"
        /"alias_dictionary.json"
    )

    # JSON 파일 읽기
    with open(alias_path, "r", encoding="utf-8") as file:
        alias_dict = json.load(file)
    
    return alias_dict


# create_alias_lookup: Alias Dictionary를 역방향 조회 구조로 변환
def create_alias_lookup(alias_dict: dict) -> dict:
    """
    표준 컬럼 기준 Alias Dictionary를 alias 기준 조회 딕셔너리로 변환

    Args:
        alias_dict (dict): 표준 컬럼별 alias 목록
    
    Returns:
        dict: alias를 key, 표준 컬럼을 value로 가지는 딕셔너리
    
    Raises:
        없음
    """

    # alias 조회 딕셔너리
    alias_lookup = {}

    # alias를 정규화한 후 standard_column으로 변환해 저장
    for standard_column, aliases in alias_dict.items():
        for alias in aliases:
            normalized_alias = normalize_column_name(alias)
            alias_lookup[normalized_alias] = standard_column
    
    return alias_lookup


# Alias Dictionary 로드
COLUMN_ALIAS_DICT = load_alias_dictionary()


# Alias Lookup 생성
ALIAS_LOOKUP = create_alias_lookup(COLUMN_ALIAS_DICT)


# map_column_by_alias: Alias Dictionary 기반 단일 컬럼 매핑
def map_column_by_alias(normalized_column: str) -> dict:
    """
    Alias Dictionary 기준으로 단일 컬럼을 표준 컬럼에 매핑

    Args:
        normalized_column (str): 정규화된 컬럼명
    
    Returns:
        dict: 매핑 결과
    
    Raises:
        없음
    """


    # alias 존재 여부 확인
    if normalized_column in ALIAS_LOOKUP:
        return {
            "mapped_to" : ALIAS_LOOKUP[normalized_column],
            "confidence" : 1.0,
            "source" : ["alias"],
            "confirmed" : False
        }
    
    # 미매핑 상태 반환
    return {
        "mapped_to" : None,
        "confidence" : 0.0,
        "source" : [],
        "confirmed" : False
    }


# map_columns_by_alias: 전체 컬럼 Alias Dictionary 매핑 수행
def map_columns_by_alias(columns: list) -> dict:
    """
    전체 컬럼에 대해 Alias Dictionary 매핑 수행

    Args:
        columns (list): 원본 컬럼 리스트
    
    Returns:
        dict: 전체 컬럼 매핑 결과
    
    Raises:
        없음
    """

    # 컬럼 정규화
    normalized_columns = normalize_columns(columns)

    # 결과 저장
    mapping_result = {}

    # 정규화된 컬럼 반복 매핑
    for source_column, normalized_column in normalized_columns.items():
        alias_result = map_column_by_alias(normalized_column)

        mapping_result[source_column] = {
            "normalized_column" : normalized_column,
            "mapped_to" : alias_result["mapped_to"],
            "confidence" : alias_result["confidence"],
            "source" : alias_result["source"],
            "confirmed" : alias_result["confirmed"]
        }
    
    return mapping_result