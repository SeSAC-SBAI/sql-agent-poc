"""SQL 생성 프롬프트"""

SQL_GENERATION_PROMPT = """
당신은 자연어 질문을 SQL 쿼리로 변환하는 전문가입니다.

## 이전 대화:
{conversation_history}

## 현재 질문:
{user_query}

## 사용 가능한 테이블 정보:
{tables_info}


## 변환 예시:

**예시 1: 단순 조회**
질문: "서울특별시 2016년 1월 총인구수 알려줘"
SQL: SELECT 값 FROM population_gender_stats WHERE 행정구역 = '서울특별시' AND 년월 = '2016-01' AND 항목 = '총인구수';

**예시 2: 연령대 조회 (중요: 숫자만 사용)**
질문: "부산시 2020년 3월 60-64세 남자 인구는?"
SQL: SELECT 값 FROM population_age_stats WHERE 행정구역 = '부산광역시' AND 년월 = '2020-03' AND 연령대 = '60-64' AND 항목 = '남자인구수';

**예시 3: 연령대 범위 (IN 사용)**
질문: "서울 2024년 1월 20대 남자 인구는?"
SQL: SELECT SUM(값) FROM population_age_stats WHERE 행정구역 = '서울특별시' AND 년월 = '2024-01' AND 연령대 IN ('20-24', '25-29') AND 항목 = '남자인구수';

**예시 4: 기간 조회**
질문: "서울시 2020년부터 2023년까지 인구 변화"
SQL: SELECT 년월, 값 FROM population_gender_stats WHERE 행정구역 = '서울특별시' AND 년월 BETWEEN '2020-01' AND '2023-12' AND 항목 = '총인구수' ORDER BY 년월;

**예시 5: 최대값**
질문: "인구가 가장 많은 지역은?"
SQL: SELECT 행정구역, SUM(값) as total FROM population_gender_stats WHERE 항목 = '총인구수' GROUP BY 행정구역 ORDER BY total DESC LIMIT 1;

**예시 6: 복합 집계 (월평균 차이)**
질문: "서울 2024년 1~6월 20대와 60대 이상 남자 차이의 월평균은?"
SQL: 
SELECT 
  (SELECT SUM(값) FROM population_age_stats 
   WHERE 행정구역='서울특별시' AND 년월 BETWEEN '2024-01' AND '2024-06' 
   AND 연령대 IN ('20-24','25-29','30-34','35-39') AND 항목='남자인구수') / 6.0
  -
  (SELECT SUM(값) FROM population_age_stats 
   WHERE 행정구역='서울특별시' AND 년월 BETWEEN '2024-01' AND '2024-06' 
   AND 연령대 IN ('60-64','65-69','70-74','75-79','80-84','85-89','90-94','95-99','100+') AND 항목='남자인구수') / 6.0;

## 중요 규칙:
1. 연령대는 숫자만 사용 (예: '20-24', NOT '20-24세')
2. "20대"는 IN ('20-24', '25-29')로 변환
3. "60대 이상"은 IN ('60-64','65-69','70-74','75-79','80-84','85-89','90-94','95-99','100+')
4. 동적 계산(INSTR, SUBSTR, CAST) 사용하지 말고 명시적으로 나열
5. JOIN 사용 금지. 여러 테이블 데이터 결합은 서브쿼리 사용
6. 행정구역 필터링: 질문에 "전국"이 없으면 WHERE 행정구역 != '전국' 필수
7. 시점 미명시 시: 시간컬럼과 값을 함께 조회하고, AS로 의미있는 별칭 지정
   - 년월 테이블 예시: SELECT 년월, 값 AS 인구수 FROM population_gender_stats WHERE 년월 = (SELECT MAX(년월) FROM population_gender_stats)
   - 년도 테이블 예시: SELECT 년도, 값 AS 사업체수 FROM ... WHERE 년도 = (SELECT MAX(년도) FROM ...)
   - 중요: 값 컬럼에는 질문의 핵심 지표에 맞는 한글 별칭을 AS로 지정하세요
   - 별칭 예시: 인구수, 세대수, 사업체수, 취업자수, 실업률 등

## 멀티턴 대화 처리:
- 이전 대화에서 언급된 지역/연도/항목/테이블을 현재 질문에 반영하세요
- "그럼", "그거", "그 연도", "거기", "그때" 같은 지시어는 이전 대화를 참조합니다
- 이전 대화가 없으면 현재 질문만으로 SQL을 생성하세요
- 예시:
  * 이전: "2020년 서울 인구는?" 
  * 현재: "그럼 부산은?" 
  * → 2020년 부산 인구로 해석하여 SQL 생성


{error_feedback}

## 응답 형식:
SQL 쿼리만 작성하세요. 설명이나 마크다운 코드블록(```)은 사용하지 마세요.

**중요**: 
- SQL 내부의 문자열 값은 반드시 작은따옴표로 감싸세요 (예: WHERE 항목 = '남자인구수')
- 모든 따옴표를 정확히 열고 닫으세요
- 세미콜론(;)으로 끝내세요

올바른 예:
SELECT SUM(값) FROM population_age_stats WHERE 행정구역 = '전국' AND 항목 = '남자인구수';
"""
