"""
confing_loader.py

config/ 폴더의 JSON 설정 파일을 로드하는 모듈

기능:
    - config/ 폴더의 JSON 설정 파일 로드
    - 프로젝트 루트 기준 경로 자동 계산
    - alias_dictionary, rule_patterns, standard_columns 로드 함수 제공
    - 타입별 컬럼 목록 조회
    - 분석 모듈별 필수 컬럼 목록 조회
    - 전체 표준 컬럼 목록 조회
"""


import json
from pathlib import Path
from functools import lru_cache


# 프로젝트 루트 경로 계산
PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_DIR = PROJECT_ROOT / "config"


# _load_json: JSON 파일을 로드하는 함수
def _load_json(file_name: str) -> dict:
    """
    config/ 폴더에서 JSON 파일을 로드하는 내부 함수입니다.

    Args:
        file_name (str): 로드할 JSON 파일명
    
    Returns:
        dict: JSON 파일 내용
    
    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
        json.JSONDecodeError: JSON 형식이 올바르지 않은 경우
    """

    # JSON 파일 경로 지정
    file_path = CONFIG_DIR / file_name

    # 파일이 해당 경로에 없을 시 에러
    if not file_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {file_path}")
    
    # 해당 경로의 파일을 불러오기
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
    


# load_alias_dictionary: alias_dictionary를 로드하는 함수
# 캐싱 설정
@lru_cache(maxsize=None)
def load_alias_dictionary() -> dict:
    """
    alias_dictionary.json을 로드합니다.

    Returns:
        dict: 표준 컬럼별 alias 목록
    
    Raises:
        FileNotFoundError: 파일이 존재하지 않을 경우
        json.JSONDecodeError: JSON 형식이 올바르지 않은 경우
    """

    # 지정한 내부 함수를 활용하여 alias_dictionary 로드
    return _load_json("alias_dictionary.json")


# load_rule_patterns: rule_patterns를 로드하는 함수
# 캐싱 설정
@lru_cache(maxsize=None)
def load_rule_patterns() -> dict:
    """
    rule_patterns.json을 로드합니다.

    Returns:
        dict: 표준 컬럼별 Rule-Based 패턴 정보
    
    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
        json.JSONDecodeError: JSON 형식이 올바르지 않은 경우
    """

    # 지정한 내부 함수를 활용하여 rule_patterns 로드
    return _load_json("rule_patterns.json")


# load_standard_columns: standard_columns를 로드하는 함수
# 캐싱 설정
@lru_cache(maxsize=None)
def load_standard_columns() -> dict:
    """
    standard_columns.json을 로드합니다.

    Returns:
        dict: 표준 컬럼별 타입, 필수 여부, grain, category 정보
    
    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
        json.JSONDecodeError: JSON 형식이 올바르지 않은 경우
    """

    # 지정한 내부 함수를 활용하여 standard_columns 로드
    return _load_json("standard_columns.json")


# get_columns_by_type: 특정 타입에 해당하는 표준 컬럼 목록 반환
def get_columns_by_type(column_type: str) -> list:
    """
    특정 타입에 해당하는 표준 컬럼 목록을 반환합니다.

    Args:
        column_type (str): 조회할 타입 (예: "date", "numeric", "integer", "boolean")
    
    Returns:
        list: 해당 타입의 표준 컬럼 목록
    
    Raises:
        없음
    """

    # standard_columns.json을 로드
    standard_columns = load_standard_columns()

    # 타입별 조회
    return [col for col, info in standard_columns.items() if info["type"] == column_type]


# get_columns_required_for: 특정 분석 모듈에서 필수인 표준 컬럼 목록 반환
def get_columns_required_for(module: str) -> list:
    """
    특정 분석 모듈에서 필수인 표준 컬럼 목록을 반환합니다.

    Args:
        module (str): 조회할 분석 모듈 (예: "kpi", "cohort", "rfm", "product", "delivery")
    
    Returns:
        list: 해당 분석 모듈의 필수 컬럼 목록
    
    Raises:
        없음
    """

    # standard_columns.json을 로드
    standard_columns = load_standard_columns()

    # 분석 모듈별 조회
    return [col for col, info in standard_columns.items() if module in info["required_for"]]


# get_standard_column_list: 전체 표준 컬럼 목록 반환
def get_standard_column_list() -> list:
    """
    전체 표준 컬럼 목록을 반환합니다.
    
    Args:
        없음
    
    Returns:
        list: 전체 표준 컬럼 목록 (None 포함)
    
    Raises:
        없음
    """

    # standard_columns.json을 로드
    standard_columns = load_standard_columns()

    # 표준 컬럼 목록 반환
    return [None] + list(standard_columns.keys())