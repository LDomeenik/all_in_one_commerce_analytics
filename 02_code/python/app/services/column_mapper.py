"""
column_mapper.py

업로드 데이터의 컬럼을 표준 컬럼으로 매핑하기 위한 모듈

기능:
    - 원본 컬럼명 정규화
    - Alias Dictionary JSON 로드
    - Rule-Based Pattern JSON 로드
    - Alias Dictionary 기반 컬럼 매핑
    - Rule-Based 컬럼 매핑
    - Alias + Rule-Based 통합 컬럼 매핑
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

    if not isinstance(column_name, str):
        raise TypeError("컬럼명은 문자열이어야 합니다.")

    normalized = column_name.strip()
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)
    normalized = normalized.lower()
    normalized = re.sub(r"[\s\-.]+", "_", normalized)

    if re.search(r"[가-힣]", normalized):
        normalized = normalized.replace("_", "")

    normalized = re.sub(r"_+", "_", normalized)
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


# load_json_config: config 폴더의 JSON 파일 로드
def load_json_config(file_name: str) -> dict:
    """
    config 폴더에 있는 JSON 설정 파일을 로드

    Args:
        file_name (str): 로드할 JSON 파일명

    Returns:
        dict: JSON 파일 내용

    Raises:
        FileNotFoundError: JSON 파일이 존재하지 않는 경우 발생
        json.JSONDecodeError: JSON 파일 형식이 올바르지 않은 경우 발생
    """

    config_path = (
        Path(__file__)
        .resolve()
        .parents[2]
        / "config"
        / file_name
    )

    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)

    return config


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

    return load_json_config("alias_dictionary.json")


# load_rule_patterns: JSON 파일에서 Rule-Based 패턴을 로드
def load_rule_patterns() -> dict:
    """
    JSON 파일에서 Rule-Based 매핑 패턴을 로드

    Args:
        없음

    Returns:
        dict: 표준 컬럼별 Rule-Based 패턴 정보

    Raises:
        FileNotFoundError: Rule Pattern JSON 파일이 존재하지 않는 경우 발생
        json.JSONDecodeError: Rule Pattern JSON 파일 형식이 올바르지 않은 경우 발생
    """

    return load_json_config("rule_patterns.json")


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

    alias_lookup = {}

    for standard_column, aliases in alias_dict.items():
        for alias in aliases:
            normalized_alias = normalize_column_name(alias)
            alias_lookup[normalized_alias] = standard_column

    return alias_lookup


# Alias Dictionary 로드
COLUMN_ALIAS_DICT = load_alias_dictionary()


# Alias Lookup 생성
ALIAS_LOOKUP = create_alias_lookup(COLUMN_ALIAS_DICT)


# Rule Pattern 로드
RULE_PATTERNS = load_rule_patterns()


# map_column_by_alias: Alias Dictionary 기반 단일 컬럼 매핑
def map_column_by_alias(normalized_column: str) -> dict:
    """
    Alias Dictionary 기준으로 단일 컬럼을 표준 컬럼에 매핑

    Args:
        normalized_column (str): 정규화된 컬럼명

    Returns:
        dict: Alias Dictionary 매핑 결과

    Raises:
        없음
    """

    if normalized_column in ALIAS_LOOKUP:
        return {
            "mapped_to": ALIAS_LOOKUP[normalized_column],
            "confidence": 1.0,
            "source": ["alias"],
            "confirmed": False
        }

    return {
        "mapped_to": None,
        "confidence": 0.0,
        "source": [],
        "confirmed": False
    }


# map_column_by_rule: 정규화된 컬럼명을 Rule-Based 방식으로 표준 컬럼 후보에 매핑
def map_column_by_rule(normalized_column: str) -> dict:
    """
    정규화된 컬럼명을 Rule-Based 패턴 기준으로 표준 컬럼 후보에 매핑

    Args:
        normalized_column (str): 정규화된 원본 컬럼명

    Returns:
        dict: Rule-Based 매핑 결과

    Raises:
        없음
    """

    for standard_column, rule_info in RULE_PATTERNS.items():
        patterns = rule_info.get("patterns", [])
        confidence = rule_info.get("confidence", 0.7)

        for pattern in patterns:
            if re.search(pattern, normalized_column):
                return {
                    "mapped_to": standard_column,
                    "confidence": confidence,
                    "source": ["rule"],
                    "confirmed": False
                }

    return {
        "mapped_to": None,
        "confidence": 0.0,
        "source": [],
        "confirmed": False
    }


# map_columns_by_alias: 전체 컬럼 Alias Dictionary 매핑 수행
def map_columns_by_alias(columns: list) -> dict:
    """
    전체 컬럼에 대해 Alias Dictionary 매핑 수행

    Args:
        columns (list): 원본 컬럼 리스트

    Returns:
        dict: 전체 컬럼 Alias Dictionary 매핑 결과

    Raises:
        없음
    """

    normalized_columns = normalize_columns(columns)
    mapping_result = {}

    for source_column, normalized_column in normalized_columns.items():
        alias_result = map_column_by_alias(normalized_column)

        mapping_result[source_column] = {
            "normalized_column": normalized_column,
            "mapped_to": alias_result["mapped_to"],
            "confidence": alias_result["confidence"],
            "source": alias_result["source"],
            "confirmed": alias_result["confirmed"]
        }

    return mapping_result


# map_columns: Alias + Rule-Based 통합 컬럼 매핑 수행
def map_columns(columns: list) -> dict:
    """
    전체 컬럼에 대해 Alias + Rule-Based 통합 매핑 수행

    Args:
        columns (list): 원본 컬럼 리스트

    Returns:
        dict: 전체 컬럼 통합 매핑 결과

    Raises:
        없음
    """

    normalized_columns = normalize_columns(columns)
    mapping_result = {}

    for source_column, normalized_column in normalized_columns.items():
        alias_result = map_column_by_alias(normalized_column)

        if alias_result["mapped_to"] is not None:
            final_result = alias_result
        else:
            final_result = map_column_by_rule(normalized_column)

        mapping_result[source_column] = {
            "normalized_column": normalized_column,
            "mapped_to": final_result["mapped_to"],
            "confidence": final_result["confidence"],
            "source": final_result["source"],
            "confirmed": final_result["confirmed"]
        }

    return mapping_result