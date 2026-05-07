"""
file_uploader.py

업로드된 CSV / Excel 파일을 pandas DataFrame으로 변환하는 파일 입출력 모듈

기능:
    - 파일 확장자 검증
    - CSV / Excel 파일 읽기
    - pandas DataFrame 변환
    - 파일 메타데이터 생성
"""


from pathlib import Path
from datetime import datetime

import pandas as pd


# 호환 가능한 확장자명 지정
ALLOWED_EXTENSIONS = [".csv", ".xlsx", ".xls"]


# validate_file_extension: 업로드 파일의 확장자가 허용된 형식인지 검증
def validate_file_extension(file_name: str) -> str:
    """
    업로드된 파일명의 확장자를 검증

    Args:
        file_name (str): 업로드된 파일명
    
    Returns:
        str: 검증된 파일 확장자
    
    Raises:
        ValueError: 허용되지 않은 파일 확장자인 경우 발생
    """

    # 파일 확장자
    ext = Path(file_name).suffix.lower()

    # 파일 확장자명이 일치하는지 검증
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"지원하지 않는 파일 형식입니다. "
            f"지원 형식: {ALLOWED_EXTENSIONS}, 현재 파일 형식: {ext}"
        )
    
    return ext


# load_uploaded_files: 업로드된 CSV / Excel 파일을 DataFrame으로 변환
def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    """
    업로드된 파일 객체를 pandas DataFrame으로 변환

    Args:
        uploaded_files: Streamlit의 st.file_uploader()가 반환하는 업로드 파일 객체
    
    Returns:
        pd.DataFrame: 업로드된 파일을 읽어 생성한 DataFrame
    
    Raises:
        ValueError: 지원하지 않는 파일 형식이거나 파일을 읽을 수 없는 경우 발생
    """


    # 파일명
    file_name = uploaded_file.name

    # 확장자 검증
    ext = validate_file_extension(file_name)

    # 검증된 확장자가 ".csv"인 경우
    if ext == ".csv":
        df = pd.read_csv(uploaded_file)
        return df
    
    # 검증된 확장자가 ".xlsx"이나 ".xls"인 경우
    if ext in [".xlsx", ".xls"]:
        df = pd.read_excel(uploaded_file)
        return df
    
    # 지원하지 않는 파일 형식이거나 파일을 읽을 수 없는 경우
    raise ValueError("파일을 읽을 수 없습니다.")


# create_file_metadata: 업로드 파일의 기본 정보를 딕셔너리 형태로 생성
def create_file_metadata(uploaded_file, df: pd.DataFrame) -> dict:
    """
    업로드된 파일과 DataFrame을 기반으로 파일 메타데이터를 생성

    Args:
        uploaded_file: Streamlit의 st.file_uploader()가 반환하는 업로드 파일 객체
        df (pd.DataFrame): 업로드된 파일을 읽어 생성한 DataFrame
    
    Returns:
        dict: 파일 기본 정보를 담은 딕셔너리
            포함 정보:
                - file_name: 업로드 파일명
                - uploaded_at: 업로드 처리 시각
                - row_count: 데이터 행 개수
                - column_count: 데이터 컬럼 개수
                - columns: 컬럼명 목록
    """

    # 딕셔너리 생성
    metadata = {
        "file_name" : uploaded_file.name,
        "uploaded_at" : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "row_count" : len(df),
        "column_count" : len(df.columns),
        "columns" : list(df.columns)
    }

    return metadata