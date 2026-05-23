
# 컬럼 매핑 정책서

```
본 문서는 다양한 이커머스 데이터셋의 컬럼을
표준 컬럼 구조로 자동 변환하기 위한 매핑 기준을 정의합니다.

컬럼 매핑은 Raw 데이터를 Staging Layer로 변환하는 과정에서 수행되며,
이후 전처리, Data Mart 구성, 분석 모듈 실행의 기준이 됩니다.

본 프로젝트는 Rule-Based 방식과 Semantic 기반 추론을 결합한
Hybrid Column Mapping Engine을 통해
자동화 수준과 정확도를 동시에 확보하는 것을 목표로 합니다.

본 프로젝트의 컬럼 매핑은 다음과 같은 단계로 수행됩니다.

1. 컬럼명 정규화
2. Alias Dictionary 매핑
3. Rule-Based 매핑
4. Data Profiling 기반 매핑
5. Relationship Detection
6. Domain Validation
7. LLM Semantic Mapping
8. Confidence Score 계산
9. Human Review
10. Mapping Memory 저장

매핑 우선순위는 다음과 같습니다.

1. Mapping Memory
2. Alias Dictionary
3. Rule-Based Mapping
4. Data Profiling
5. Relationship Detection
6. Domain Validation
7. LLM Semantic Mapping
8. Confidence Score
9. Human Review
```


---

## 1. 컬럼명 정규화

```
컬럼명 정규화는 원본 데이터의 컬럼명을 표준 컬럼 및 
Alias Dictionary와 비교 가능한 형태로 변환하기 위한 전처리 단계입니다.

본 단계에서는 컬럼명 표기 방식의 차이로 인해 동일 의미 컬럼이
서로 다른 값으로 인식되는 문제를 제거합니다.

정규화 기준은 다음과 같습니다.

- 공백 제거
- 소문자 변환
- CamelCase 변환
- 특수문자 변환
- 중복 구분자 정리
- 한글 컬럼 처리
```

- **정규화 기준**

| 처리 항목            | 설명                          | 예시                           |
| :--------------- | --------------------------- | ---------------------------- |
| **공백 제거**        | 컬럼명 앞뒤 공백 제거                | `" order_id"` → `order_id`   |
| **소문자 변환**       | 영문 컬럼명을 소문자로 변환             | `ORDER_ID` → `order_id`      |
| **CamelCase 변환** | 붙어 있는 영문 단어를 snake_case로 변환 | `orderDate` → `order_date`   |
| **특수문자 변환**      | 공백, 하이픈, 점 등을 '_'로 변환       | `order-date` → `order_date`  |
| **중복 구분자 정리**    | 연속된 '_'를 하나로 정리             | `order__date` → `order_date` |
| **한글 컬럼 처리**     | 한글 컬럼의 공백 및 특수문자 제거         | `주문 일자` → `주문일자`             |


---

## 2. Alias Dictionary 매핑

```
Alias Dictionary 매핑은 사전에 정의된 컬럼 별칭 정보를 기반으로
정규화된 컬럼명을 표준 컬럼으로 1차 매핑 단계입니다.

본 단계는 전체 매핑 과정에서 가장 높은 우선순위를 가지며,
대부분의 컬럼 매핑은 해당 단계에서 결정됩니다.
```

- **설계 구조**
	- Alias Dictionary는 표준 컬럼을 기준으로 다수의 alias를 가지는 구조로 관리

| 표준 컬럼         | Alias 목록                                  |
| ------------- | ----------------------------------------- |
| `order_id`    | `order_id`, `orderno`, `order_no`, `주문번호` |
| `order_date`  | `order_date`, `order_dt`, `주문일자`          |
| `customer_id` | `customer_id`, `user_id`, `고객id`          |
| `revenue`     | `revenue`, `total_price`, `결제금액`          |

- **처리 로직**
	- 컬럼명 정규화 수행
	- Alias Dictionary 내 포함 여부 확인
	- 일치 시 해당 표준 컬럼으로 매핑


---

## 3. Rule-Based 매핑

```
Rule-Based 매핑은 Alias Dictionary에서 매핑되지 않은 컬럼을 대상으로
컬럼명 패턴을 기반으로 표준 컬럼 후보를 생성하는 2차 매핑 단계입니다.

본 단계는 컬럼명의 구조적 특징을 활용하여
새로운 형태의 컬럼에 대해서도 매핑 가능성을 확보하는 것을 목적으로 합니다.
```

- **처리 규칙**

| 패턴                              | 설명     | 매핑 대상                               |
| :------------------------------ | ------ | ----------------------------------- |
| `*_id`                          | 식별자 형태 | ID 계열 (`order_id`, `customer_id` 등) |
| `*_date`, `*_dt`, `*_timestamp` | 날짜 형태  | `order_date`, `shipping_date` 등     |
| `amount`, `price`, `value`      | 금액 관련  | `revenue` 등                         |
| `qty`, `quantity`               | 수량     | `quantity` 등                        |
| `*_cd`, `*_code`                | 코드값    | ID 또는 코드 컬럼                         |

- **처리 로직**
	- 정규화된 컬럼명 입력
	- 정의된 패턴 규칙과 비교
	- 일치하는 규칙이 있을 경우 표준 컬럼 후보 생성


---

## 4. Data Profiling 기반 매핑

```
Data Profiling 기반 매핑은 컬럼명의 정보만으로 의미를 판단하기 어려운 경우,
컬럼 내 실제 데이터를 분석하여 표준 컬럼 후보를 추론하는 단계입니다.

본 단계는 데이터의 구조적 특성과 통계적 분포를 기반으로
컬럼의 의미를 추정하고, 매핑 후보를 생성하는 것을 목적으로 합니다.
```

- **분석 요소**

| 항목      | 설명                       |
| ------- | ------------------------ |
| **데이터 타입**  | 문자열, 숫자, 날짜 여부           |
| **NULL 비율** | 결측 데이터 비율                |
| **고유값 비율**  | unique 값 비율              |
| **값 분포**    | 값의 범위 및 분포               |
| **패턴 분석**   | 문자열 형식 (예: 날짜, ID, 패턴 등) |

- **처리 로직**
	- 컬럼 데이터 샘플 추출
	- 데이터 타입 및 분포 분석
	- 패턴 기반 의미 추론
	- 표준 컬럼 후보 생성


---

## 5. Relationship Detection

```
Relationship Detection은 다수의 테이블이 존재하는 경우
테이블 간 컬럼 관계를 분석하여 표준 컬럼 매핑 후보를 추론하는 단계입니다,

본 단계는 컬럼 단위가 아닌 데이터 구조 단위에서 의미를 파악하며,
특히 식별자(ID) 및 참조 관계(FK) 추론에 활용됩니다.

본 단계의 적용 대상은 다중 테이블 입력 데이터로 단일 테이블의 경우 스킵됩니다.
```

- **분석 요소**

| 항목          | 설명                  |
| ----------- | ------------------- |
| **공통 컬럼**       | 여러 테이블에 반복 등장하는 컬럼  |
| **Join 가능성**    | 컬럼 간 값 일치 여부        |
| **Cardinality** | 1:1, 1:N 관계         |
| **데이터 중복 여부**   | unique / non-unique |

- **처리 로직**
	- 테이블 간 공통 컬럼 탐지
	- 컬럼 값 비교를 통한 Join 가능성 분석
	- unique 비율 기반 key 후보 판단
	- 관계 구조 기반 표준 컬럼 후보 생성


---

## 6. Domain Validation

```
Domain Validation은 이전 단계에서 생성된 표준 컬럼 후보에 대해
이커머스 도메인 규칙을 기반으로 매핑의 유효성을 검증하는 단계입니다.

본 단계는 컬럼의 의미 추론 결과가 실제 데이터 구조 및 비즈니스 로직과
일치하는지를 확인하며, 잘못된 매핑을 제거하는 것을 목적으로 합니다.
```

- **검증 규칙**

| 검증 항목  | 설명                                                        |
| :----- | --------------------------------------------------------- |
| 금액 검증  | `revenue` ≈ `payment_amount` 또는 `unit_price` x `quantity` |
| 날짜 검증  | `order_date` ≤ `delivered_date`                           |
| ID 검증  | 식별자는 높은 unique 비율을 가져야 함                                  |
| 상태값 검증 | 상태 컬럼은 제한된 값 집합을 가짐                                       |

- **처리 로직**
	- 매핑 후보 컬럼 선택
	- 도메인 규칙 적용
	- 규칙 충족 여부 판단
	- 검증 실패 시 후보 제외


---

## 7. LLM Semantic Mapping

```
LLM Semantic Mapping은 기존 Rule-Based 및 Data Profiling, Domain Validation 단계에서
명확하게 결정되지 않은 컬럼에 대해 의미 기반으로 최종 후보를 선택하는 단계입니다.

본 단계는 컬럼명, 데이터 샘플, 후보 컬럼 정보를 종합하여
자연어 기반 의미 유사도를 활용한 매핑 보조 역할을 수행합니다.
```

- **입력 정보**
	- 정규화된 컬럼명
	- 데이터 샘플
	- 데이터 타입
	- 후보 컬럼 리스트

- **처리 로직**
	- 후보 컬럼 리스트 생성
	- LLM에 컬럼 정보 및 후보 전달
	- 의미 기반으로 최적 후보 선택
	- 선택 결과 및 판단 근거 반환


---

## 8. Confidence Score

```
Confidence Score는 각 매핑 단계에서 생성된 결과를 종합하여
표준 컬럼 매핑의 신뢰도를 수치화하고 최종 매핑 여부를 결정하는 단계입니다.

본 단계는 Alias, Rule-Based, Data Profiling, Relationship Detection, 
Domain Validation, LLM 결과를 통합하여 단일 점수로 변환합니다.
```

- **구성 요소**

| 항목                 | 설명                     |
| :----------------- | ---------------------- |
| Alias Score        | Alias Dictionary 일치 여부 |
| Rule Score         | 패턴 기반 매칭 정도            |
| Profiling Score    | 데이터 특성 일치도             |
| Relationship Score | 테이블 관계 기반 신뢰도          |
| Domain Score       | 도메인 검증 통과 여부           |
| LLM Score          | 의미 기반 유사도              |

- **계산 방식**
	- 각 요소에 가중치를 부여하여 최종 점수를 계산
	- $Final\quad Score = \Sigma\quad(각 요소 점수 \times 가중치)$

- **처리 기준**
	- ≥ 0.9: 자동 매핑
	- 0.7 ~ 0.9: 후보 유지
	- < 0.7: 사용자 검수 대상


---

## 9. Human Review

```
Human Review는 자동 매핑 결과에 대해 사용자가 최종 검수 및 수정할 수 있는 단계입니다.

본 단계는 자동 매핑 결과를 최종 확정하기 전에 수행되며,
Confidence Score와 관계없이 모든 매핑 결과는 사용자 수정이 가능하도록 설계합니다.

본 단계의 처리 원칙은 다음과 같습니다.

- 자동 매핑 결과는 최종 확정값이 아닌 추천값으로 처리
- 모든 컬럼은 사용자가 수정 가능
- Confidence Score가 낮은 컬럼은 검수 필요 상태로 표시
- 사용자가 확정한 매핑 결과를 최종 매핑 결과로 사용
```

- **상태 기준**

| 상태    | 조건                           | 처리         |
| :---- | ---------------------------- | ---------- |
| 자동 매핑 | Confidence Score ≥ 0.9       | 추천 매핑값 표시  |
| 확인 필요 | 0.7 ≤ Confidence Score < 0.9 | 사용자 검수 권장  |
| 검수 필요 | Confidence Score < 0.7       | 사용자 확인 필요  |
| 미매핑   | 후보 없음                        | 사용자가 직접 선택 |

- **처리 로직**
	- 자동 매핑 결과 생성
	- Confidence Score 및 매핑 근거 표시
	- 사용자 수정 또는 확정 수행
	- 최종 매핑 결과 생성


---

## 10. Mapping Memory 저장

```
Mapping Memory는 Human Review 단계에서 사용자가 최종 확정한 컬럼 매핑 결과를 저장하고,
이후 동일하거나 유사한 데이터셋이 업로드될 때 재사용하기 위한 기능입니다.

본 단계는 반복적인 사용자 검수를 줄이고, 
데이터셋이 누적될수록 매핑 정확도를 향상시키는 것을 목적으로 합니다.

기존에 Mapping Memory가 존재하는 경우 다음 매핑 실행 시 우선 적용됩니다.
```

- **저장 대상**
	- 사용자가 최종 확정한 매핑 결과
	- 사용자가 자동 매핑 결과를 수정한 결과
	- 미매핑 컬럼에 대해 사용자가 직접 지정한 결과

- **저장 항목**

| 항목                  | 설명           |
| :------------------ | ------------ |
| `source_column`     | 원본 컬럼명       |
| `normalized_column` | 정규화된 컬럼      |
| `standard_column`   | 사용자 확정 표준 컬럼 |
| `dataset_signature` | 데이터셋 식별 정보   |
| `confidence`        | 자동 매핑 당시 신뢰도 |
| `confirmed_by_user` | 사용자 확정 여부    |
| `created_at`        | 저장 시점        |

- **처리 로직**
	- Human Review 완료
	- 사용자 확정 매핑 결과 추출
	- Mapping Memory 저장
	- 이후 업로드 시 우선 매핑 후보로 활용


---

## 11. 최종 출력 구조

```
최종 컬럼 매핑 결과는 각 원본 컬럼에 대해 표준 컬럼 매핑 결과와 신뢰도, 
매핑 근거, 사용자 확정 여부를 포함하는 구조로 반환합니다.

본 구조는 이후 전처리, Data Mart 적재, 분석 모듈 실행의 기준 데이터로 활용됩니다.
```

- **출력 구조**

```json
{
	"source_column" : {
		"mapped_to" : "standard_column",
		"confidence" : 0.0,
		"source" : [],
		"confirmed" : false
	}
}
```

- **필드 정의**

| 필드              | 설명              |
| --------------- | --------------- |
| `source_column` | 원본 데이터의 컬럼명     |
| `mapped_to`     | 매핑된 표준 컬럼       |
| `confidence`    | 최종 매핑 신뢰도 (0~1) |
| `source`        | 매핑에 사용된 판단 근거   |
| `confirmed`     | 사용자 확정 여부       |

- **source 필드 정의**

| 값              | 설명                      |
| -------------- | ----------------------- |
| `alias`        | Alias Dictionary 매핑     |
| `rule`         | Rule-Based 매핑           |
| `profiling`    | Data Profiling 기반 매핑    |
| `relationship` | 테이블 관계 기반 매핑            |
| `domain`       | Domain Validation 통과    |
| `llm`          | LLM Semantic Mapping 사용 |

- **예시**

```json
{  
	"order_dt": {  
		"mapped_to": "order_date",  
		"confidence": 0.92,  
		"source": ["alias", "domain"],  
		"confirmed": true  
	},  
	"user_no": {  
		"mapped_to": "customer_id",  
		"confidence": 0.78,  
		"source": ["rule", "profiling"],  
		"confirmed": false  
	},  
	"value": {  
		"mapped_to": "revenue",  
		"confidence": 0.64,  
		"source": ["profiling", "llm"],  
		"confirmed": false  
	}  
}
```
