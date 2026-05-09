"""
column_mapping_applier.py

확정된 컬럼 매핑 결과를 DataFrame에 적용하는 모듈

기능:
    - 확정 매핑 결과에서 rename_dict 생성
    - 미매핑 컬럼 목록 추출
    - 원본 DataFrame 컬럼명을 표준 컬럼명으로 변경
    - Staging용 표준 컬럼 DataFrame 생성
"""


import pandas as pd


# build_rename_dict: 확정 매핑 결과에서 DataFrame rename용 딕셔너리 생성
def build_rename_dict(confirmed_mapping_result: dict) -> dict:
    """
    확정된 컬럼 매핑 결과에서 rename_dict를 생성

    Args:
        confirmed_mapping_result (dict): Human Review를 거친 최종 컬럼 매핑 결과
    
    Returns:
        dict: 원본 컬럼명을 표준 컬럼명으로 매핑한 딕셔너리
    
    Raises:
        없음
    """

    # rename용 딕셔너리 생성
    rename_dict = {}

    # confirm 완료된 컬럼들의 매핑 결과를 딕셔너리에 적재
    for source_column, mapping_info in confirmed_mapping_result.items():
        mapped_to = mapping_info.get("mapped_to")

        if mapped_to is not None:
            rename_dict[source_column] = mapped_to
    
    return rename_dict


# extract_unmapped_columns: 미매핑 컬럼 목록 추출
def extract_unmapped_columns(confirmed_mapping_result: dict) -> list:
    """
    확정된 컬럼 매핑 결과에서 미매핑 컬럼 목록을 추출

    Args:
        confirmed_mapping_result (dict): Human Review를 거친 최종 컬럼 매핑 결과
    
    Returns:
        list: 표준 컬럼으로 매핑되지 않은 원본 컬럼 목록
    
    Raises:
        없음
    """

    # 미매핑 컬럼 목록 생성
    unmapped_columns = []

    # "mapped_to"가 없는 컬럼들을 미매핑 컬럼 목록에 적재
    for source_column, mapping_info in confirmed_mapping_result.items():
        mapped_to = mapping_info.get("mapped_to")

        if mapped_to is None:
            unmapped_columns.append(source_column)
    
    return unmapped_columns


# apply_column_mapping: 확정 매핑 결과를 원본 DataFrmae에 적용
def apply_column_mapping(
        df: pd.DataFrame,
        confirmed_mapping_result: dict
) -> tuple[pd.DataFrame, dict, list]:
    """
    확정된 컬럼 매핑 결과를 원본 DataFrame에 적용하여 Staging용 DataFrame을 생성

    Args:
        df (pd.DataFrame): 업로드된 원본 DataFrame
        confirmed_mapping_result (dict): Human Review를 거친 최종 컬럼 매핑 결과
    
    Returns:
        tuple:
            - pd.DataFrame: 표준 컬럼명으로 변경된 Staging용 DataFrame
            - dict: rename에 사용된 컬럼 매핑 딕셔너리
            - list: 표준 컬럼으로 매핑되지 않은 원본 컬럼 목록
    
    Raises:
        ValueError: 확정된 매핑 결과가 비어 있는 경우 발생
    """

    # 확정된 매핑 결과가 비어 있는 경우
    if not confirmed_mapping_result:
        raise ValueError("확정된 컬럼 매핑 결과가 없습니다.")
    
    # 표준 컬럼명으로 매핑된 딕셔너리와 매핑되지 않은 컬럼
    rename_dict = build_rename_dict(confirmed_mapping_result)
    unmapped_columns = extract_unmapped_columns(confirmed_mapping_result)

    # staging_df 생성
    staging_df = df.rename(columns=rename_dict)

    # staging_df의 컬럼 지정
    staging_columns = list(rename_dict.values())
    staging_df = staging_df[staging_columns]

    return staging_df, rename_dict, unmapped_columns