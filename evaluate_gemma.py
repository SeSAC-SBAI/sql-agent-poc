"""
CSV 테스트 케이스에 Gemma 결과 추가
"""

import sys
import csv
import time
from pathlib import Path
from google import genai

sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from database import db_manager
from utils import search_table_metadata
import re


# Gemma 클라이언트 초기화
client = genai.Client(api_key=settings.GOOGLE_API_KEY)
MODEL_NAME = "gemma-3-27b-it"


def extract_keyword(question: str) -> str:
    """질문에서 키워드 추출"""
    prompt = f"""
    질문: {question}
    
    이 질문에서 테이블을 찾기 위한 핵심 키워드 1개만 추출하세요.
    (인구, 세대, 연령 중 하나)
    
    키워드만 답변하세요:
    """
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )
    
    return response.text.strip()


def generate_sql(question: str, table_info: str, schema_info: str) -> str:
    """SQL 쿼리 생성"""
    prompt = f"""
    당신은 SQLite 전문가입니다.
    
    **질문**: {question}
    
    **사용 가능한 테이블 정보**:
    {table_info}
    
    **테이블 스키마**:
    {schema_info}
    
    **CRITICAL SQL 작성 규칙**:
    1. SQLite 문법만 사용 (MySQL, PostgreSQL 문법 금지)
    2. SELECT 쿼리 1개만 작성
    3. 집계 함수 중첩 금지 (예: AVG(SUM(...)) 절대 금지)
    4. 평균 계산: 서브쿼리 사용 (예: SELECT AVG(월별합계) FROM (SELECT 년월, SUM(값) as 월별합계 ... GROUP BY 년월))
    5. 비율 계산: CAST(값 AS FLOAT) / 값2
    6. 모든 계산은 SQL 안에서 완료
    7. 세미콜론(;) 1개로만 끝내기
    8. 설명, 주석(--), 태그 절대 포함 금지
    9. 서브쿼리에는 별칭(alias) 필수 (예: ) AS subquery)
    10. 여러 월 필터링: IN 절 사용 (예: 년월 IN ('2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06'))
    11. LIKE 패턴에서 정규표현식([]) 사용 금지
    12. CTE 사용 시: WITH 절로 시작해야 함 (예: WITH T1 AS (...), T2 AS (...) SELECT ...)
    13. 중앙값(median) 같은 복잡한 계산은 가능한 피하고, 평균이나 합계로 대체
    
    **날짜 필터링 예시**:
    잘못된 예: 년월 LIKE '2023-0[1-6]%' (SQLite에서 작동 안함!)
    올바른 예: 년월 IN ('2023-01', '2023-02', '2023-03', '2023-04', '2023-05', '2023-06')
    올바른 예: 년월 BETWEEN '2023-01' AND '2023-06'
    
    **CTE 사용 예시**:
    올바른 예: WITH T1 AS (SELECT ...), T2 AS (SELECT ...) SELECT * FROM T1 JOIN T2 ...
    잘못된 예: SELECT ... ), T2 AS (SELECT ...) (WITH 없이 시작)
    
    **SQLite에서 사용 불가능한 함수 (절대 사용 금지)**:
    - STDEV(), STDDEV() → 대신 SQRT(AVG(값*값) - AVG(값)*AVG(값)) 사용
    - VARIANCE() → 대신 (AVG(값*값) - AVG(값)*AVG(값)) 사용
    - MEDIAN() → 대신 다른 방법 사용 또는 계산 생략
    
    **SQLite에서 사용 가능한 집계 함수**:
    - COUNT(), SUM(), AVG(), MIN(), MAX(), GROUP_CONCAT()
    - 기본 산술: +, -, *, /, SQRT(), ABS(), ROUND()
    
    **집계 함수 중첩 예시**:
    잘못된 예: SELECT AVG(SUM(값)) ... (오류!)
    올바른 예: SELECT AVG(합계) FROM (SELECT SUM(값) as 합계 ... GROUP BY 년월) AS sub
    
    CRITICAL: 실행 가능한 SQLite 쿼리 1개만 작성하세요.
    
    SQL:
    """
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )
    
    sql_query = response.text.strip()
    
    # SQL 정리
    if "```" in sql_query:
        parts = sql_query.split("```")
        for part in parts:
            if part.strip().upper().startswith(('SELECT', 'WITH')):
                sql_query = part
                break
        if sql_query.startswith("sql"):
            sql_query = sql_query[3:]
    
    # 태그 및 주석 제거
    sql_query = re.sub(r'<[^>]+>', '', sql_query)
    lines = sql_query.split('\n')
    cleaned_lines = []
    for line in lines:
        if '--' in line:
            line = line.split('--')[0]
        if line.strip():
            cleaned_lines.append(line.strip())
    sql_query = ' '.join(cleaned_lines)
    
    # 첫 번째 세미콜론까지
    if ';' in sql_query:
        sql_query = sql_query.split(';')[0] + ';'
    
    # SELECT/WITH 시작 확인
    sql_query = sql_query.strip()
    if not (sql_query.upper().startswith('SELECT') or sql_query.upper().startswith('WITH')):
        select_idx = sql_query.upper().find('SELECT')
        with_idx = sql_query.upper().find('WITH')
        
        if select_idx != -1 and with_idx != -1:
            start_idx = min(select_idx, with_idx)
        elif with_idx != -1:
            start_idx = with_idx
        elif select_idx != -1:
            start_idx = select_idx
        else:
            start_idx = 0
            
        if start_idx > 0:
            sql_query = sql_query[start_idx:]
    
    sql_query = ' '.join(sql_query.split())
    
    return sql_query


def evaluate_test_cases(input_csv: str):
    """
    테스트 케이스 실행 및 결과 저장
    """
    
    # 설정 검증 및 DB 연결
    settings.validate()
    db = db_manager.get_db()
    
    # 출력 파일명
    model_name = MODEL_NAME.replace("/", "_").replace(".", "_").replace("-", "_")
    output_csv = f"result_lv3_{model_name}.csv"
    
    print(f"\n사용 모델: {MODEL_NAME}")
    print(f"결과 파일: {output_csv}\n")
    
    # CSV 읽기
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        test_cases = list(reader)
    
    results = []
    
    print(f"총 {len(test_cases)}개 테스트 케이스 실행 중...\n")
    
    for i, case in enumerate(test_cases, 1):
        question = case['input']
        expected_query = case['query']
        expected_label = case['label']
        
        print(f"[{i}/{len(test_cases)}] {question[:50]}...")
        
        try:
            # 1. 키워드 추출
            keyword = extract_keyword(question)
            print(f"   키워드: {keyword}")
            
            # 2. 메타데이터 검색
            table_info = search_table_metadata.invoke({"keywords": keyword})
            
            # 3. 스키마 정보
            schema_info = db.get_table_info()
            
            # 4. SQL 생성
            generated_query = generate_sql(question, table_info, schema_info)
            print(f"   쿼리: {generated_query[:80]}...")
            
            # 5. SQL 실행
            try:
                sql_result = db.run(generated_query)
                generated_answer = str(sql_result).strip('[]()').strip()
            except Exception as e:
                generated_answer = f"ERROR: {str(e)}"
                
        except Exception as e:
            generated_query = "ERROR"
            generated_answer = str(e)
        
        # 결과 저장
        results.append({
            'input': question,
            'expected_query': expected_query,
            'generated_query': generated_query,
            'expected_label': expected_label,
            'generated_answer': generated_answer
        })
        
        print(f"   답변: {generated_answer[:80]}...")
        print()
        
        # API rate limit 방지
        time.sleep(5)
    
    # CSV로 저장
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['input', 'expected_query', 'generated_query', 
                     'expected_label', 'generated_answer']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n✅ 결과 저장 완료: {output_csv}")
    
    # 간단한 통계
    success_count = sum(1 for r in results if 'ERROR' not in r['generated_query'])
    print(f"\n📊 통계:")
    print(f"   총 테스트: {len(results)}개")
    print(f"   성공: {success_count}개")
    print(f"   실패: {len(results) - success_count}개")


if __name__ == "__main__":
    input_file = "population_test_lv3_v1.1.csv"
    evaluate_test_cases(input_file)