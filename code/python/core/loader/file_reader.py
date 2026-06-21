"""
file_reader.py

업로드된 CSV / Excel 파일을 pandas DataFrame으로 변환하는 모듈

기능:
    - 파일 확장자 검증
    - CSV / Excel 파일을 DataFrame으로 변환
    - 다중 파일을 {파일명: DataFrame} 딕셔너리로 변환
    - 파일 메타데이터 생성
"""


from pathlib import Path
from datetime import datetime

import pandas as pd


# 허용 확장자 정의
ALLOWED_EXTENSIONS = [".csv", ".xlsx", ".xls"]


# validate_file_extension: 파일 확장자 검증
def validate_file_extension(file_name: str) -> str:
    """
    업로드된 파일의 확장자를 검증합니다.

    Args:
        file_name (str): 업로드된 파일명

    Returns:
        str: 검증된 파일 확장자

    Raises:
        ValueError: 허용되지 않은 확장자인 경우
    """

    # 파일 확장자 추출 및 소문자 변환
    ext = Path(file_name).suffix.lower()

    # 허용되지 않은 확장자인 경우 에러 발생
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"지원하지 않는 파일 형식입니다. "
            f"지원 형식: {ALLOWED_EXTENSIONS}, 현재 파일 형식: {ext}"
        )

    return ext


# read_file: 단일 파일 읽기
def read_file(file) -> pd.DataFrame:
    """
    파일 객체를 pandas DataFrame으로 변환합니다.

    Args:
        file: 파일 객체
            - Streamlit의 st.file_uploader() 반환값
            - 또는 로컬 파일 경로 (str / Path)

    Returns:
        pd.DataFrame: 파일을 읽어 생성한 DataFrame

    Raises:
        ValueError: 지원하지 않는 파일 형식인 경우
        Exception: 파일을 읽는 중 오류가 발생한 경우
    """

    # 파일 객체와 로컬 경로 모두 지원하기 위해 파일명 추출 방식 분기
    if hasattr(file, "name"):
        file_name = file.name
    else:
        file_name = Path(file).name

    # 확장자 검증 (지원하지 않는 형식이면 ValueError 발생)
    ext = validate_file_extension(file_name)

    # CSV 파일 읽기
    if ext == ".csv":
        return pd.read_csv(file)

    # Excel 파일 읽기
    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(file)


# read_multiple_files: 다중 파일 읽기
def read_multiple_files(files: list) -> dict[str, pd.DataFrame]:
    """
    여러 파일을 읽어 {파일명: DataFrame} 딕셔너리로 반환합니다.

    Args:
        files (list): 파일 객체 리스트 (st.file_uploader의 반환값)

    Returns:
        dict[str, pd.DataFrame]: {파일명: DataFrame}

    Raises:
        ValueError: 지원하지 않는 파일 형식인 경우
    """

    result = {}

    # 파일 리스트 순회하며 각 파일 읽기
    for file in files:
        # 확장자 사전 검증 (read_file 내부에서도 검증되지만 명시적으로 먼저 확인)
        validate_file_extension(file.name)

        # 파일명을 키로, DataFrame을 값으로 저장
        result[file.name] = read_file(file)

    return result


# create_file_metadata: 단일 파일 메타데이터 생성
def create_file_metadata(file, df: pd.DataFrame) -> dict:
    """
    파일과 DataFrame을 기반으로 메타데이터를 생성합니다.

    Args:
        file: 파일 객체 또는 로컬 파일 경로
        df (pd.DataFrame): 파일을 읽어 생성한 DataFrame

    Returns:
        dict: 파일 메타데이터
            - file_name (str): 파일명
            - uploaded_at (str): 업로드 처리 시각
            - row_count (int): 데이터 행 개수
            - column_count (int): 데이터 컬럼 개수
            - columns (list): 컬럼명 목록

    Raises:
        없음
    """

    # 파일 객체와 로컬 경로 모두 지원하기 위해 파일명 추출 방식 분기
    if hasattr(file, "name"):
        file_name = file.name
    else:
        file_name = Path(file).name

    return {
        "file_name": file_name,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns)
    }