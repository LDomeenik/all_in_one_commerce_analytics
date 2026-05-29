"""
diagnosis_page.py

분석 가능 여부 진단 UI 페이지 모듈

기능:
    - 전처리 완료 데이터 기반 진단 실행
    - 분석 모듈별 실행 가능 여부 출력
    - 필수 컬럼 결측 비율 출력
    - 선택 컬럼 존재 여부 출력
    - 진단 결과 session_state 저장
"""


import streamlit as st

from core.diagnostics.diagnosis import diagnose, ANALYSIS_MODULES
from app.streamlit.session import (
    get_state,
    set_state,
    PREPROCESSED_DF,
    DIAGNOSIS_RESULT
)


# render_diagnosis_page: 진단 페이지 렌더링
def render_diagnosis_page():
    """
    분석 가능 여부 진단 페이지를 렌더링합니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    st.subheader("4단계. 분석 가능 여부 진단")

    # 전처리 완료 여부 확인
    preprocessed_df = get_state(PREPROCESSED_DF)

    if preprocessed_df is None:
        st.warning("먼저 전처리를 완료해주세요.")
        return
    
    # 진단 실행
    if get_state(DIAGNOSIS_RESULT) is None:
        with st.spinner("진단 중..."):
            try:
                diagnosis_result = diagnose(preprocessed_df)
                set_state(DIAGNOSIS_RESULT, diagnosis_result)
                st.rerun()
            except ValueError as e:
                st.error(f"진단 중 오류가 발생했습니다: {e}")
        
        return
    
    # 진단 결과 출력
    _render_diagnosis_result()


# _render_diagnosis_result: 진단 결과 출력 내장 함수
def _render_diagnosis_result():
    """
    진단 결과를 화면에 출력합니다.

    Args:
        없음
    
    Returns:
        없음
    
    Raises:
        없음
    """

    diagnosis_result = get_state(DIAGNOSIS_RESULT)

    # 전체 요약
    total = len(diagnosis_result)
    available = sum(
        1 for result in diagnosis_result.values()
        if result["available"]
    )

    st.write("#### 진단 요약")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("전체 분석 모듈", total)
    with col2:
        st.metric("실행 가능", available)
    with col3:
        st.metric("실행 불가", total - available)
    
    st.divider()

    # 모듈별 진단 결과 출력
    st.write("#### 분석 모듈별 진단 결과")

    for module, result in diagnosis_result.items():
        module_name = ANALYSIS_MODULES[module]
        _render_module_result(module_name, result)
    
    # 재진단 버튼
    st.divider()
    if st.button("재진단"):
        set_state(DIAGNOSIS_RESULT, None)
        st.rerun()


# _render_module_result: 단일 모듈 진단 결과 출력 내장 함수
def _render_module_result(module_name: str, result: dict):
    """
    단일 분석 모듈의 진단 결과를 출력합니다.

    Args:
        module_name (str): 분석 모듈 이름
        result (dict): 진단 결과

    Returns:
        없음

    Raises:
        없음
    """

    available = result["available"]
    status = result["status"]
    missing_columns = result["missing_columns"]
    optional_missing = result["optional_missing"]
    null_rate = result["null_rate"]

    # 상태에 따른 아이콘
    icon = "✅" if available else "❌"

    with st.expander(f"{icon} {module_name} ({status})"):

        # 실행 불가인 경우 필수 컬럼 안내
        if not available:
            st.error(f"필수 컬럼 누락: {missing_columns}")

        # 결측 비율 출력 (0% 제외)
        non_zero_null = {
            col: rate for col, rate in null_rate.items()
            if rate > 0
        }

        if non_zero_null:
            st.write("**필수 컬럼 결측 비율**")
            for column, rate in non_zero_null.items():
                if rate <= 30:
                    st.warning(f"🟡 `{column}`: {rate}% 결측")
                else:
                    st.error(f"🔴 `{column}`: {rate}% 결측 (주의 필요)")

        # 선택 컬럼 누락 안내
        if optional_missing:
            st.write("**누락된 선택 컬럼** (있으면 분석이 풍부해집니다.)")

            cols = st.columns(3)
            for i, column in enumerate(optional_missing):
                with cols[i % 3]:
                    st.markdown(f"- `{column}`")