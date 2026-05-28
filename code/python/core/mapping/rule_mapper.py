"""
rule_mapper.py

Rule-Based 패턴 기반으로 컬럼을 표준 컬럼에 매핑하는 모듈

기능:
    - rule_patterns.json의 정규식 패턴 기반 단일 컬럼 매핑
    - 전체 컬럼 목록 Rule-Based 매핑
"""


import re

from core.loader.config_loader import load_rule_patterns


# map_column_by_rule: 단일 컬럼 Rule-Based 매핑
def map_column_by_rule(normalized_column: str) -> dict:
    """
    정규화된 컬럼명을 Rule-Based 패턴 기준으로 표준 컬럼에 매핑합니다.

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

    # rule_pattern 로드
    rule_patterns = load_rule_patterns()

    # 각 표준 컬럼의 패턴과 비교
    for standard_column, rule_info in rule_patterns.items():
        patterns = rule_info.get("patterns", [])
        confidence = rule_info.get("confidence", 0.75)

        for pattern in patterns:
            if re.search(pattern, normalized_column):
                return {
                    "mapped_to": standard_column,
                    "confidence": confidence,
                    "source": ["rule"]
                }
    
    return {
        "mapped_to": None,
        "confidence": 0.0,
        "source": []
    }