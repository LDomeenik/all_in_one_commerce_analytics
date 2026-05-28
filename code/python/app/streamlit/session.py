"""
session.py

Streamlit session_state 중앙 관리 모듈

기능:
    - session_state 키 상수 정의
    - session_state 초기화
    - session_state 데이터 저장 및 조회
"""


import streamlit as st


# session_state 키 상수 정의
RAW_DF = "raw_df"
FILE_METADATA = "file_metadata"
MAPPING_RESULT = "mapping_result"
CONFIRMED_MAPPING = "confirmed_mapping"
STAGING_DF = "staging_df"
RENAME_DICT = "rename_dict"
UNMAPPED_COLUMNS = "unmapped_columns"


# init_session: session_state 초기화
def init_session():
    """
    session_state를 초기값으로 초기화합니다. 이미 존재하는 키는 덮어쓰지 않습니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    # session_state 초기화
    defaults = {
        RAW_DF: None,
        FILE_METADATA: None,
        MAPPING_RESULT: None,
        CONFIRMED_MAPPING: None,
        STAGING_DF: None,
        RENAME_DICT: None,
        UNMAPPED_COLUMNS: []
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# set_State: session_state에 값 저장
def set_state(key: str, value):
    """
    session_state에 값을 저장합니다.

    Args:
        key (str): session_state 키
        value: 저장할 값
    
    Returns:
        없음
    
    Raises:
        없음
    """

    st.session_state[key] = value


# get_state: session_state에서 값 조회
def get_state(key: str):
    """
    session_state에서 값을 조회합니다.

    Args:
        key (str): session_state 키
    
    Returns:
        저장된 값 또는 None
    
    Raises:
        없음
    """

    return st.session_state.get(key)