"""
mapping_result_view.py

컬럼 매핑 결과 화면 출력 모듈

기능:
    - 컬럼 매핑 결과를 DataFrame으로 변환
    - 미매핑 컬럼 개수 계산
    - Confidence Score 기준 상태 생성
    - 사용자가 매핑 결과를 직접 수정 (최종 확정)
    - 최종 확정 매핑 결과 반환
"""


import pandas as pd
import streamlit as st


# 각 분석 모듈의 필수 컬럼 정의
STANDARD_COLUMNS = [
    None,
    "order_id",
    "order_item_id",
    "order_date",
    "customer_id",
    "customer_name",
    "product_id",
    "product_name",
    "product_category",
    "brand_name",
    "quantity",
    "unit_price",
    "revenue",
    "discount_amount",
    "shipping_fee",
    "payment_method",
    "order_status",
    "seller_id",
    "seller_name",
    "shipped_date",
    "delivered_date",
    "review_score",
    "review_count"
]


# get_review_status: confidence 기준 검수 상태 반환
def get_review_status(confidence: float, mapped_to: str | None) -> str:
    """
    Confidence Score와 매핑 여부를 기준으로 검수 상태를 반환

    Args:
        confidence (float): 컬럼 매핑 신뢰도
        mapped_to (str | None): 매핑된 표준 컬럼명
    
    Returns:
        str: 검수 상태
    
    Raises:
        없음
    """

    # 매핑 상황별 return 값
    if mapped_to is None:
        return "미매핑"
    
    if confidence >= 0.9:
        return "자동 매핑"
    
    if confidence >= 0.7:
        return "확인 필요"
    
    return "검수 필요"


# convert_mapping_result_to_dataframe: 컬럼 매핑 결과를 화면 출력용 DataFrame으로 변환
def convert_mapping_result_to_dataframe(mapping_result: dict) -> pd.DataFrame:
    """
    컬럼 매핑 결과 딕셔너리를 Streamlit 출력용 DataFrame으로 변환

    Args:
        mapping_result (dict): 원본 컬럼별 컬럼 매핑 결과
    
    Returns:
        pd.DataFrame: 컬럼 매핑 결과 DataFrame
    
    Raises:
        없음
    """

    # 딕셔너리를 DtaFrame으로 변환
    mapping_df = pd.DataFrame.from_dict(
        mapping_result,
        orient="index"
    )

    # index를 일반 컬럼으로 변환
    mapping_df = mapping_df.reset_index()

    # 컬럼명 변경
    mapping_df = mapping_df.rename(
        columns={
            "index" : "source_column"
        }
    )

    # Confidence Score 기반 검수 상태 컬럼 생성
    mapping_df["review_status"] = mapping_df.apply(
        lambda row: get_review_status(
            row["confidence"],
            row["mapped_to"]
        ),
        axis=1
    )

    return mapping_df


# count_unmapped_columns: 미매핑 컬럼 개수 계산
def count_unmapped_columns(mapping_df: pd.DataFrame) -> int:
    """
    컬럼 매핑 결과에서 미매핑 컬럼 개수를 계산

    Args:
        mapping_df (pd.DataFrmae): 컬럼 매핑 결과 DataFrame
    
    Returns:
        int: 미매핑 컬럼 개수
    
    Raises:
        없음
    """

    # mapped_to가 비어 있는 컬럼 수 계산
    unmapped_count = mapping_df["mapped_to"].isna().sum()

    return unmapped_count


# build_confirmed_mapping_result: 사용자 선택값을 최종 매핑 결과로 변환
def build_confirmed_mapping_result(
        mapping_df: pd.DataFrame,
        user_selected_mapping: dict
) -> dict:
    """
    사용자 검수 결과를 최종 컬럼 매핑 결과 딕셔너리로 변환

    Args:
        mapping_df (pd.DataFrame): 자동 매핑 결과 DataFrame
        user_selected_mapping (dict): 사용자가 선택한 최종 매핑값
    
    Returns:
        dict: 최종 확정 컬럼 매핑 결과
    
    Raises:
        없음
    """

    # 최종 확정 컬럼 매핑 결과 저장용 딕셔너리 생성
    confirmed_mapping_result = {}

    # 각 컬럼별 사용자 선택 결과를 최종 매핑 결과에 반영
    for _, row in mapping_df.iterrows():
        source_column = row["source_column"]
        selected_column = user_selected_mapping[source_column]

        # 사용자 확정 결과 저장
        confirmed_mapping_result[source_column] = {
            "normalized_column" : row["normalized_column"],
            "mapped_to" : selected_column,
            "confidence" : row["confidence"],
            "source" : row["source"],
            "confirmed" : True if selected_column is not None else False
        }

    return confirmed_mapping_result


# render_mapping_result: 컬럼 매핑 결과를 Streamlit 화면에 출력
def render_mapping_result(mapping_result: dict):
    """
    컬럼 매핑 결과를 Streamlit 화면에 출력

    Args:
        mapping_result (dict): 원본 컬럼별 컬럼 매핑 결과
    
    Returns:
        pd.DataFrame: 컬럼 매핑 결과 DataFrame
    
    Raises:
        없음
    """

    # mapping 데이터프레임 지정
    mapping_df = convert_mapping_result_to_dataframe(mapping_result)

    # mapping되지 않은 컬럼 개수 지정
    unmapped_count = count_unmapped_columns(mapping_df)

    # 섹션 구분
    st.divider()
    st.subheader("2. 컬럼 매핑 사용자 검수")

    st.write(
        "자동 매핑 결과를 확인한 뒤, 잘못 매핑된 컬럼은 직접 수정해주세요."
    )

    st.dataframe(mapping_df)

    # 미매핑 컬럼 개수에 따른 행동
    if unmapped_count == 0:
        st.success("모든 컬럼이 자동 매핑되었습니다. 필요 시 수정 후 확정해주세요.")
    else:
        st.warning(f"미매핑 컬럼이 {unmapped_count}개 있습니다. 직접 선택해주세요.")
    
    st.write("### 최종 매핑 선택")

    # 사용자 선택 결과 저장용 딕셔너리 생성
    user_selected_mapping = {}

    # 각 컬럼별 표준 컬럼 선택 UI 생성
    for _, row in mapping_df.iterrows():
        source_column = row["source_column"]
        mapped_to = row["mapped_to"]

        # 자동 매핑 결과가 존재할 경우 기본 선택값 지정
        if mapped_to in STANDARD_COLUMNS:
            default_index = STANDARD_COLUMNS.index(mapped_to)
        else:
            default_index = 0
        
        # 사용자 선택용 표준 컬럼 SelectBox 생성
        selected_column = st.selectbox(
            label=f"{source_column} → 표준 컬럼 선택",
            options=STANDARD_COLUMNS,
            index=default_index,
            key=f"mapping_select_{source_column}"
        )

        # 사용자 선택 결과 저장
        user_selected_mapping[source_column] = selected_column

    # 사용자가 최종 매핑 확정 버튼을 클릭한 경우
    if st.button("최종 매핑 확정"):
        confirmed_mapping_result = build_confirmed_mapping_result(
            mapping_df=mapping_df,
            user_selected_mapping=user_selected_mapping
        )

        st.success("최종 컬럼 매핑이 확정되었습니다.")

        st.write("### 최종 확정 매핑 결과")
        st.json(confirmed_mapping_result)

        return confirmed_mapping_result

    return None